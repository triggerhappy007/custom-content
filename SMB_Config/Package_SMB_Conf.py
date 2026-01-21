import os


file_source = "//etc//samba//smb.conf"
#file_source = "smb.conf"
file_dest = file_source + ".tan"

section_global = 0
client_max_protocol = 0
client_min_protocol = 0
encrypt_passwords = 0
smb_encrypt = 0
smb_signing = 0

if os.path.isfile(file_source) == True:
        if os.path.isfile(file_dest) == True:
                os.remove(file_dest)
        os.rename(file_source, file_dest)
        
        destination = open(file_source, "w")
        source = open(file_dest, "r")
        
        for line in source:
                
                if "[global]" in line:
                        print("Starting global section")
                        section_global = 1
                else:
                        if "[" in line and section_global == 1 and "[global]" not in line:
                                
                                if client_max_protocol == 0:
                                        print("adding line : \tclient max protocol = SMB3_11\n")
                                        destination.write("\tclient max protocol = SMB3_11\n")
                                if client_min_protocol == 0:
                                        print("adding line : \tclient min protocol = SMB3\n")
                                        destination.write("\tclient min protocol = SMB3\n")
                                if encrypt_passwords == 0:
                                        print("adding line : \tencrypt passwords = yes\n")
                                        destination.write("\tencrypt passwords = yes\n")
                                if smb_encrypt == 0:
                                        print("adding line : \tsmb encrypt = required\n")
                                        destination.write("\tsmb encrypt = required\n")
                                if smb_signing == 0:
                                        print("adding line : \tsmb signing = required\n")
                                        destination.write("\tsmb signing = required\n")
                                section_global = 0
                                print("End of global section not editing rest of file")

                if "client max protocol" in line:
                        print("changing line : ",line)
                        destination.write("\tclient max protocol = SMB3_11\n")
                        client_max_protocol=1
                elif "client min protocol" in line:
                        print("changing line : ",line)
                        destination.write("\tclient min protocol = SMB3\n")
                        client_min_protocol = 1
                elif "encrypt passwords" in line:
                        print("changing line : ",line)
                        destination.write("\tencrypt passwords = yes\n")
                        encrypt_passwords = 1
                elif "smb encrypt" in line:
                        print("changing line : ",line)
                        destination.write("\tsmb encrypt = required\n")
                        smb_encrypt = 1
                elif "smb signing" in line:
                        print("changing line : ",line)
                        destination.write("\tsmb signing = required\n")
                        smb_signing = 1
                else:
                        destination.write(line)

        source.close()
        destination.close()
else:
        print("smb.conf not present")
