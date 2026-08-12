import os
from flask import Flask, request, jsonify, send_from_directory, redirect
from functools import wraps
from dotenv import load_dotenv
from auth_service import AuthService
from vacation_service import VacationService
from db_service import DatabaseService

load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')
auth_service = AuthService()
vacation_service = VacationService()
db = DatabaseService()


# Helper: Token authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Authentication token is missing'}), 401

        token_payload = auth_service.verify_request_token(token)
        if not token_payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        from flask import g
        g.user = token_payload
        return f(*args, **kwargs)
    return decorated


# Helper: Role check decorator
def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            from flask import g
            if not auth_service.token_verifier.has_role(g.user, required_role):
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


# Development/Test Login (temporarily available when OIDC is not configured)
@app.route('/api/auth/login', methods=['POST'])
def test_login():
    """Simple login endpoint for development/testing without OIDC."""
    data = request.get_json()
    username = data.get('username')
    
    if not username:
        return jsonify({'error': 'Username required'}), 400
    
    user = db.get_user_by_username(username)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    roles = db.get_user_roles(user['id'])
    token = auth_service.token_verifier.create_token(user['id'], user['username'], roles)
    return jsonify({'token': token})


# Routes
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/login')
def login():
    """Redirect to OIDC provider."""
    auth_url = auth_service.get_authorization_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    """Handle OAuth/OIDC callback."""
    code = request.args.get('code')
    if not code:
        return send_from_directory('../frontend', 'callback.html')

    token = auth_service.handle_callback(code)
    if not token:
        return jsonify({'error': 'Authentication failed'}), 401

    response = jsonify({'token': token})
    return response


# API Routes
@app.route('/api/user/profile', methods=['GET'])
@token_required
def get_profile():
    from flask import g
    user = db.get_user_by_id(g.user['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    # Add roles to the profile
    user_dict = dict(user)
    user_dict['roles'] = [r['name'] for r in db.get_user_roles(user['id'])]
    return jsonify(user_dict)


@app.route('/api/vacation/requests', methods=['POST'])
@token_required
def create_vacation_request():
    from flask import g
    data = request.get_json()
    result = vacation_service.create_request(
        user_id=g.user['user_id'],
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        reason=data.get('reason', ''),
        request_type=data.get('request_type', 'FULL_DAY'),
        start_time=data.get('start_time', '09:00:00'),
        end_time=data.get('end_time', '17:00:00')
    )
    if not result['success']:
        return jsonify(result), 400
    return jsonify(result), 201


@app.route('/api/vacation/requests', methods=['GET'])
@token_required
def get_vacation_requests():
    from flask import g
    requests_list = vacation_service.get_user_requests(g.user['user_id'])
    return jsonify([dict(r) for r in requests_list])


@app.route('/api/vacation/pending', methods=['GET'])
@token_required
@role_required('MANAGER')
def get_pending_requests():
    from flask import g
    pending = vacation_service.get_pending_for_manager(g.user['user_id'])
    return jsonify([dict(r) for r in pending])


@app.route('/api/vacation/approve/<int:request_id>', methods=['POST'])
@token_required
@role_required('MANAGER')
def approve_request(request_id):
    from flask import g
    result = vacation_service.approve_request(request_id, g.user['user_id'])
    return jsonify(result)


@app.route('/api/vacation/reject/<int:request_id>', methods=['POST'])
@token_required
@role_required('MANAGER')
def reject_request(request_id):
    from flask import g
    result = vacation_service.reject_request(request_id, g.user['user_id'])
    return jsonify(result)


@app.route('/api/vacation/balance', methods=['GET'])
@token_required
def get_balance():
    from flask import g
    year = request.args.get('year', type=int)
    balance = vacation_service.get_balance(g.user['user_id'], year)
    if balance:
        # Convert SQLite Row to dict
        columns = balance.keys()
        return jsonify(dict(zip(columns, balance)))
    return jsonify({})


# Admin routes
@app.route('/api/admin/users', methods=['GET'])
@token_required
@role_required('ADMIN')
def get_users():
    users = db.get_all_users()
    result = []
    for user in users:
        user_dict = dict(user)
        user_dict['roles'] = [r['name'] for r in db.get_user_roles(user['id'])]
        result.append(user_dict)
    return jsonify(result)


@app.route('/api/admin/users/<int:user_id>/roles', methods=['POST'])
@token_required
@role_required('ADMIN')
def assign_role(user_id):
    data = request.get_json()
    role_name = data.get('role')
    if not role_name:
        return jsonify({'error': 'Role name required'}), 400
    db.assign_role_to_user(user_id, role_name)
    return jsonify({'success': True})


@app.route('/api/admin/users/<int:user_id>/manager', methods=['PUT'])
@token_required
@role_required('ADMIN')
def set_manager(user_id):
    data = request.get_json()
    manager_id = data.get('manager_id')
    db.update_user_manager(user_id, manager_id)
    return jsonify({'success': True})


@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@token_required
@role_required('ADMIN')
def deactivate_user(user_id):
    db.delete_user(user_id)
    return jsonify({'success': True})


if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(host=host, port=port, debug=debug)
