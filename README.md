
The purpose of this project is to create a sample HR vacation application. You can another of my projects as an example. The sample can be found here:
https://github.com/tim1e9/agentry/tree/main/vacay

If you cannot access the internet, please tell me.

This application should be written in Python using either flask or fastapi. You should create a virtual environment so that things don't get installed into the global space.

The front end should not use a heavyweight framework like React or Angular; just use css, javascript and well structured html.

Your first step is to generate a list of tasks to do. Please generate them into a file named TASKS.md. Once generated, you should loop through them and prioritize them. Next, implement the tasks until you are done.

Some additional information:
- Use sqlite for the database
- We will use oauth / oidc for the flow, but I don't yet have the oidc provider configured, so just plan for this. I will add the provider before we're done.
- Roles / groups will come from the provider. Consider there to be the following roles: EMPLOYEE, MANAGER, ADMIN.

One extra request: During long-running work, do not remain silent for extended periods. If a task is still in progress, emit a brief visible progress update at least once every 5 minutes, then continue working without waiting for my confirmation. The update can be partial; do not delay it until the task is complete.
