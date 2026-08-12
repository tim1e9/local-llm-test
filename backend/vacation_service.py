from db_service import DatabaseService
from datetime import datetime


class VacationService:
    def __init__(self):
        self.db = DatabaseService()

    def calculate_hours(self, start_date, end_date, start_time='09:00:00', end_time='17:00:00'):
        """Calculate vacation hours between dates and times."""
        start = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M:%S")
        delta = end - start
        # Calculate working hours (8 hours per day)
        total_days = delta.days + 1
        return total_days * 8

    def create_request(self, user_id, start_date, end_date, reason, request_type='FULL_DAY', start_time='09:00:00', end_time='17:00:00'):
        """Create a new vacation request."""
        hours = self.calculate_hours(start_date, end_date, start_time, end_time)

        # Check balance
        year = datetime.strptime(start_date, '%Y-%m-%d').year
        balance = self.db.get_vacation_balance(user_id, year)
        if balance:
            available = balance['balance_hours'] - balance['used_hours']
            if hours > available:
                return {'success': False, 'error': f'Insufficient vacation balance. Available: {available} hours'}

        request_id = self.db.create_vacation_request(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            hours_requested=hours,
            reason=reason,
            request_type=request_type,
            start_time=start_time,
            end_time=end_time
        )
        return {'success': True, 'request_id': request_id}

    def get_user_requests(self, user_id):
        """Get all vacation requests for a user."""
        return self.db.get_user_vacation_requests(user_id)

    def get_pending_for_manager(self, manager_id):
        """Get pending requests for users managed by this manager."""
        return self.db.get_pending_requests_for_manager(manager_id)

    def approve_request(self, request_id, manager_id):
        """Approve a vacation request."""
        self.db.approve_request(request_id, manager_id)
        return {'success': True}

    def reject_request(self, request_id, manager_id):
        """Reject a vacation request."""
        self.db.reject_request(request_id, manager_id)
        return {'success': True}

    def get_balance(self, user_id, year=None):
        """Get vacation balance for a user."""
        return self.db.get_vacation_balance(user_id, year)
