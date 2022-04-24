import subprocess

processes = []

while True:
    action = input('start - запуск, quit - выход, kill - закрыть процессы: ')

    if action == 'quit':
        break
    elif action == 'start':
        processes.append(subprocess.Popen('python .\server\\async_server.py'))
        
        processes.append(subprocess.Popen(f'python ./client/client.py -n Sergei'))
        processes.append(subprocess.Popen(f'python ./client/client.py -n Olga'))

    elif action == 'kill':
        while processes:
            to_kill = processes.pop()
            to_kill.kill()