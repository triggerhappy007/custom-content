# ============================================================
# Sensor : Unknown
# OS     : Windows  |  Language: Python
# Desc   : Collecting the list of Office Add-Ins Details
See https://docs.microsoft.com/en-us/office/dev/add-ins/overview/office-add-ins
The sensor will report the Office Add-Ins in the registry with User Name and detailed reg key
# ============================================================

# Office Add-Ins details sensor
# Version = 1.0
# TAM - Laurent Chappe 20201005

import winreg
import os
import platform
import tanium


def GetUserName(sid):
    
    try:       
        sid=sid.upper()      
        sid=sid.partition("\\SOFTWARE\\MICROSOFT\\")[0]
        Registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        RegName = r"SYSTEM\CurrentControlSet\Control\hivelist"
        RawKey = winreg.OpenKey(Registry, RegName)
        sid_full= "\\REGISTRY\\USER\\" + sid
        result = winreg.QueryValueEx(RawKey, sid_full)[0]
        sid_name=result.strip("\\NTUSER.DAT")
        sid_name=sid_name.partition("\\Users\\")[2]
        
    except WindowsError:
        sid_name = "Error Extracting SID"
        pass
    return sid_name
    

def check_registry_HKUSERS(RegName):   
    try:
        Registry = winreg.ConnectRegistry(None, winreg.HKEY_USERS)
        RawKey = winreg.OpenKey(Registry, RegName)
        
        i = 0
        while True:
            Addin_key = winreg.EnumKey(RawKey,i)
            Addin_name=winreg.OpenKey(RawKey, Addin_key)
            i += 1
            try:
                FriendlyName = str(winreg.QueryValueEx(Addin_name,'FriendlyName')[0])
            except WindowsError:
                FriendlyName = "No Friendly Name"
            try:
                LoadBehavior= str(winreg.QueryValueEx(Addin_name,'LoadBehavior')[0])
            except WindowsError:
                LoadBehavior = "No Entry"
            result = str(Addin_key)+"|"+FriendlyName+"|"+LoadBehavior+"|"+str(RegName)+"|"+str(GetUserName(RegName))
            
            tanium.results.add(result)

    except WindowsError:
        pass
   
def reg_users():
    try:
        key = winreg.OpenKey(winreg.HKEY_USERS, r'', 0, winreg.KEY_READ)
        for i in range(0, winreg.QueryInfoKey(key)[0]):
            for x in RegKeyTuppleHKLM:
                HKUSERS_RegName = str(winreg.EnumKey(key, i)) +"\\"+ x

                check_registry_HKUSERS(HKUSERS_RegName)
    except WindowsError:
        pass




def check_registry_HKCU(RegName):   
    try:
        Registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        RawKey = winreg.OpenKey(Registry, RegName)
        i = 0
        while True:
            Addin_key = winreg.EnumKey(RawKey,i)
            Addin_name=winreg.OpenKey(RawKey, Addin_key)
            i += 1
            result = str(Addin_key)+"|"+str(winreg.QueryValueEx(Addin_name,'FriendlyName')[0])+"|"+str(winreg.QueryValueEx(Addin_name,'LoadBehavior')[0])+"|"+str(RegName)+"| Current User"
            
            tanium.results.add(result)
    except WindowsError:
        pass

def check_registry_HKLM(RegName):   
    try:
        Registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        RawKey = winreg.OpenKey(Registry, RegName)
        i = 0
        while True:
            
            Addin_key = winreg.EnumKey(RawKey,i)
            
            Addin_name=winreg.OpenKey(RawKey, Addin_key)
            
            try:
                FriendlyName = str(winreg.QueryValueEx(Addin_name,'FriendlyName')[0])
            except WindowsError:
                FriendlyName = "No Friendly Name"
            try:
                LoadBehavior= str(winreg.QueryValueEx(Addin_name,'LoadBehavior')[0])
            except WindowsError:
                LoadBehavior = "No Entry"
            i += 1
            result = str(Addin_key)+"|"+FriendlyName+"|"+LoadBehavior+"|"+str(RegName)+"| Local Machine"
            
            tanium.results.add(result)
    except WindowsError:
##        print("TSE-Error: Windows Error when extracting data")
##        tanium.results.add("TSE-Error: Windows Error when extracting data")
        pass

RegKeyTuppleHKLM = ("SOFTWARE\Microsoft\Office\Outlook\Addins","SOFTWARE\Microsoft\Office\Word\Addins","SOFTWARE\Microsoft\Office\Excel\Addins","SOFTWARE\Microsoft\Office\MS Project\Addins","SOFTWARE\Microsoft\Office\OneNote\Addins","SOFTWARE\Wow6432Node\Microsoft\Office\Visio\Addins")
RegKeyTuppleHKLM64 = ("SOFTWARE\Wow6432Node\Microsoft\Office\Outlook\Addins","SOFTWARE\Wow6432Node\Microsoft\Office\Word\Addins","SOFTWARE\Wow6432Node\Microsoft\Office\Excel\Addins","SOFTWARE\Wow6432Node\Microsoft\Office\MS Project\Addins","SOFTWARE\Wow6432Node\Microsoft\Office\PowerPoint\Addins","SOFTWARE\Wow6432Node\Microsoft\Office\OneNote\Addins","SOFTWARE\Wow6432Node\Microsoft\Office\Visio\Addins")


def sensor_main():

    
    try:
        os.environ["PROGRAMFILES(X86)"]
        for x in RegKeyTuppleHKLM64:
            check_registry_HKLM(x)
    except:
        for x in RegKeyTuppleHKLM:
            check_registry_HKLM(x)

    reg_users()


if __name__ == '__main__':
    tanium.timeout_seconds = 3
    sensor_main()


# ============================================================
# Sensor : Unknown
# OS     : Windows  |  Language: Python
# Desc   : Collecting the list of Office Add-Ins Summary
See https://docs.microsoft.com/en-us/office/dev/add-ins/overview/office-add-ins

The sensor will report a simple view of the Office Add-Ins listed in registry.
# ============================================================

# Office Add-Ins Summary sensor
# Version = 1.0
# TAM - Laurent Chappe 20201005

import winreg
import os
import platform
import tanium


def GetUserName(sid):
    
    try:       
        sid=sid.upper()      
        sid=sid.partition("\\SOFTWARE\\MICROSOFT\\")[0]
        Registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        RegName = r"SYSTEM\CurrentControlSet\Control\hivelist"
        RawKey = winreg.OpenKey(Registry, RegName)
        sid_full= "\\REGISTRY\\USER\\" + sid
        result = winreg.QueryValueEx(RawKey, sid_full)[0]
        sid_name=result.strip("\\NTUSER.DAT")
        sid_name=sid_name.partition("\\Users\\")[2]
        
    except WindowsError:
        sid_name = "Error Extracting SID"
        pass
    return sid_name
    

def check_registry_HKUSERS(RegName):   
    try:
        Registry = winreg.ConnectRegistry(None, winreg.HKEY_USERS)
        RawKey = winreg.OpenKey(Registry, RegName)
        
        i = 0
        while True:
            Addin_key = winreg.EnumKey(RawKey,i)
            Addin_name=winreg.OpenKey(RawKey, Addin_key)
            i += 1
            try:
                FriendlyName = str(winreg.QueryValueEx(Addin_name,'FriendlyName')[0])
            except WindowsError:
                FriendlyName = "No Friendly Name"
            try:
                LoadBehavior= str(winreg.QueryValueEx(Addin_name,'LoadBehavior')[0])
            except WindowsError:
                LoadBehavior = "No Entry"
            #result = str(Addin_key)+"|"+FriendlyName+"|"+LoadBehavior+"|"+str(RegName)+"|"+str(GetUserName(RegName))
            result = str(Addin_key)+"|"+FriendlyName+"|"+LoadBehavior
            
            tanium.results.add(result)

    except WindowsError:
        pass
   
def reg_users():
    try:
        key = winreg.OpenKey(winreg.HKEY_USERS, r'', 0, winreg.KEY_READ)
        for i in range(0, winreg.QueryInfoKey(key)[0]):
            for x in RegKeyTuppleHKLM:
                HKUSERS_RegName = str(winreg.EnumKey(key, i)) +"\\"+ x
##                print (HKUSERS_RegName)
                check_registry_HKUSERS(HKUSERS_RegName)
    except WindowsError:
        pass




def check_registry_HKCU(RegName):   
    try:
        Registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        RawKey = winreg.OpenKey(Registry, RegName)
        i = 0
        while True:
            Addin_key = winreg.EnumKey(RawKey,i)
            Addin_name=winreg.OpenKey(RawKey, Addin_key)
            i += 1
            #result = str(Addin_key)+"|"+str(winreg.QueryValueEx(Addin_name,'FriendlyName')[0])+"|"+str(winreg.QueryValueEx(Addin_name,'LoadBehavior')[0])+"|"+str(RegName)+"| Current User"
            result = str(Addin_key)+"|"+str(winreg.QueryValueEx(Addin_name,'FriendlyName')[0])+"|"+str(winreg.QueryValueEx(Addin_name,'LoadBehavior')[0])
            tanium.results.add(result)
    except WindowsError:
        pass

def check_registry_HKLM(RegName):   
    try:
        Registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        RawKey = winreg.OpenKey(Registry, RegName)
        i = 0
        while True:
            
            Addin_key = winreg.EnumKey(RawKey,i)
            
            Addin_name=winreg.OpenKey(RawKey, Addin_key)
            
            try:
                FriendlyName = str(winreg.QueryValueEx(Addin_name,'FriendlyName')[0])
            except WindowsError:
                FriendlyName = "No Friendly Name"
            try:
                LoadBehavior= str(winreg.QueryValueEx(Addin_name,'LoadBehavior')[0])
            except WindowsError:
                LoadBehavior = "No Entry"
            i += 1
            #result = str(Addin_key)+"|"+FriendlyName+"|"+LoadBehavior+"|"+str(RegName)+"| Local Machine"
            result = str(Addin_key)+"|"+FriendlyName+"|"+LoadBehavior
            
            tanium.results.add(result)
    except WindowsError:
##        print("TSE-Error: Windows Error when extracting data")
##        tanium.results.add("TSE-Error: Windows Error when extracting data")
        pass

RegKeyTuppleHKLM = ("SOFTWARE\Microsoft\Office\Outlook\Addins","SOFTWARE\Microsoft\Office\Word\Addins","SOFTWARE\Microsoft\Office\Excel\Addins","SOFTWARE\Microsoft\Office\MS Project\Addins","SOFTWARE\Microsoft\Office\OneNote\Addins","SOFTWARE\Wow6432Node\Microsoft\Office\Visio\Addins")
RegKeyTuppleHKLM64 = ("SOFTWARE\Wow6432Node\Microsoft\Office\Outlook\Addins","SOFTWARE\Wow6432Node\Microsoft\Office\Word\Addins","SOFTWARE\Wow6432Node\Microsoft\Office\Excel\Addins","SOFTWARE\Wow6432Node\Microsoft\Office\MS Project\Addins","SOFTWARE\Wow6432Node\Microsoft\Office\PowerPoint\Addins","SOFTWARE\Wow6432Node\Microsoft\Office\OneNote\Addins","SOFTWARE\Wow6432Node\Microsoft\Office\Visio\Addins")


def sensor_main():

    
    try:
        os.environ["PROGRAMFILES(X86)"]
        for x in RegKeyTuppleHKLM64:
            check_registry_HKLM(x)
    except:
        for x in RegKeyTuppleHKLM:
            check_registry_HKLM(x)

    reg_users()


if __name__ == '__main__':
    tanium.timeout_seconds = 3
    sensor_main()
