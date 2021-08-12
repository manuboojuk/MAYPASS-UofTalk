from flask_socketio import emit, join_room, leave_room
from app import socketio, driver, app

@socketio.on('join_room')
def handle_join_room_event(data):
    driver.add_user_to_room(data['room'], data['username'])
    app.logger.info("{} has joined chat room {}".format(data['username'], data['room']))
    join_room(data['room'])
    emit('join_room_announcement', data, room=data['room'])
    emit('public_join_room_announcement', data, broadcast=True)


@socketio.on('leave_room')
def handle_leave_room_event(data):
    driver.delete_user_from_room(data['room'], data['username'])
    app.logger.info("{} has left the room {}".format(data['username'], data['room']))
    leave_room(data['room'])
    emit('leave_room_announcement', data, room=data['room'])
    emit('public_leave_room_announcement', data, broadcast=True)


@socketio.on('send_message')
def handle_send_message(data):
    driver.send_message(data['room'], data['username'], data['message'])
    app.logger.info("{} has send message to room {}: {}".format(data['username'], data['room'], data['message']))
    emit('receive_message', data, room=data['room'])