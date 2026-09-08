import subprocess as sb
# import Popen, PIPE

PWSH = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"

result = sb.run("echo 'This is simpler'", shell=True, executable=PWSH)
sb.run("ssh user_ieee@ieeeRasp", shell=True, executable=PWSH)
process = sb.Popen(PWSH,
                shell=True,
                stdin=sb.PIPE,
                stdout=sb.PIPE,
                stderr=sb.PIPE,
                text=True)
# stdout, stderr = process.communicate('Get-Location')
# print(stdout)
# stdout, stderr = process.communicate('cd ../')
# stdout, stderr = process.communicate('Get-Location')
