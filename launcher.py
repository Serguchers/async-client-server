import subprocess

processes = []

while True:
    action = input('start - запуск, quit - выход, kill - закрыть процессы: ')

    if action == 'quit':
        break
    elif action == 'start':
        processes.append(subprocess.Popen('python async_server.py', creationflags=subprocess.CREATE_NEW_CONSOLE))
        for i in range(5):
            processes.append(subprocess.Popen(f'python client.py -n test{i}', creationflags=subprocess.CREATE_NEW_CONSOLE))

    elif action == 'kill':
        while processes:
            to_kill = processes.pop()
            to_kill.kill()