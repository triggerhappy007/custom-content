import subprocess
#import tanium

try:

    command = 'dsregcmd /status'
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    output=result.stdout

    output=output.replace(":", "|")
    lines = output.splitlines()

    keywords = ["AzureAdJoined", "EnterpriseJoined", "DomainJoined","DomainName","Virtual Desktop","TenantName","TenantId","WorkplaceTenantId","WorkplaceTenantName"]
    print(len(lines))
    for n in lines:
        if any(word in n for word in keywords):
            print(n)
            #tanium.results.add(n)
except:
    import traceback
    print(traceback.format_exc())
    tanium.results.add(traceback.format_exc())