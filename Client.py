import socket
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
import os
from tkinter.ttk import*
from tkinter import*


# Define all functions needed at the start of the code
#Written by:Joseph Chahine
def log_event(result, file_name, event):
    conn = sqlite3.connect(str(log_file_path / "Logs.db"))  # Connect to the Logs.db database stored in the user-specified directory
    cursor = conn.cursor()  # Create a cursor object to interact with the database
    local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get the current time in a readable format (for timestamping the log)

    # Format the log message as a single text block
    formatted_log = (
        f"\n"
        f"[{local_time}]\n"
        f"Event: {event}\n"
        f"File Name: {file_name}\n"
        f"Result: {result}\n"
        f"----------------------------------------\n"
    )

    # Insert the log message into the logs table
    cursor.execute("""
        INSERT INTO logs (formatted_msg)
        VALUES (?)
    """, (formatted_log,))

    conn.commit()  # Save the log entry to the database
    conn.close()   # Close the connection to avoid memory leaks

directory = input("Enter directory where you want logs stored: ") # user inputs where they want the database to be stored
log_file_path = Path(r"", directory) # specifies the file path
if not log_file_path.exists():
    print("Directory does not exist. Please check the path.")
    exit()  

#Written by:Joseph Chahine
# Help by: Makram El Hadi
def setup_database():
    conn = sqlite3.connect(str(log_file_path / "Logs.db"))  # Connect to the database (or create it if it doesn't exist)
    cursor = conn.cursor()  # Create a cursor to execute SQL statements

    cursor.execute("""CREATE TABLE IF NOT EXISTS logs (
            formatted_msg TEXT);""")
    # Table: logs — stores all log entries in one formatted text column

    cursor.execute("""CREATE TABLE IF NOT EXISTS files_info (
            file_name TEXT  NOT NULL,
            file_id INTEGER NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_size INTEGER NOT NULL, 
            last_received_byte INTEGER,
            client_hash TEXT);""")
    # Table: files_info — tracks file downloads and uploads with metadata:
    #  file_name: name of the file
    # file_id: unique identifier for matching/resuming transfers
    # upload_date: timestamp of upload (defaults to current time)
    # file_size: full file size
    # last_received_byte: how much of the file has been received (for resuming)
    # client_hash: hash to verify integrity

    conn.commit()  # Save all changes to the database
    conn.close()   # Close the connection to free resources


setup_database() # sets up the database at the start of the code
print ("Logs Setup Successfully") # prints that logs where setup successfully


'''-----------------------------------------------------------------------------------------------------------------------------------------------------  
--------------------------------------------------------------------------------------------------------------------------------------------------------'''  

# Written by: Makram El Hadi 
# Help by: Hassan Takruri
def upload_files():

    while True:

        file_path = input("Enter the file path you want to upload: ").strip(' &"\'') # Get the directory directly from the user
                                                                                    # use the .strip() to remove any spaces, the
                                                                                    # and character, the both the single and double
                                                                                    #  quotation at the start and the end of the string
        file_path = Path(file_path)
        if file_path.exists() and file_path.is_file():
            break
        else:
            print("Invalid file path. Please try again")
           
    file_name = os.path.basename(file_path) # gets the name of the file (used later to send to the server)

    file = open(file_path, "rb") # opens specified file
    file_size = os.path.getsize(file_path) # gets file size 
    client.send(file_name.encode('utf-8') + b'\n'+ str(file_size).encode('utf-8') + b'\n') # sends the file name and the file size with
                                                                                           # with an extra byte at the end to signify
                                                                                           # the end of the string (file_name or file_size)
 
    master = Tk() # initialize progress bar
    master.title(f"Uploading {file_name}")
    prog = Progressbar(master,
                       orient=HORIZONTAL,
                       length=300,
                       mode='determinate',
                       maximum=file_size)  # give progress bar parameters like pixel length and title
    prog.pack(padx=10, pady=10)
    
    sha_256 = hashlib.sha256() # hash object || actually performs the hashing algorithm based on the sha-256 way and gets updated
                               # using .update (used below)

    sent = 0 # initialize the sent data to 0
    while sent < file_size: # keeps going untill full file is sent
        packet = file.read(1024) # reads the specified number of bytes || automatically increments to the next chunk after each 
                                 # each iteration. The function .read() knows from where to continue.
        sha_256.update(packet) # updates the hashing function and it's value depending on the bytes of the packet
        client.send(packet) # send the packet read
        sent = sent + len(packet) # increment the number of packets read and sent 
        prog['value'] = sent  # set value to sent data
        master.update() # update progress bar
    master.destroy() # remove window of progress bar
    checksum = sha_256.hexdigest() # .hexdigest() return the final value of the hash 
    client.send(checksum.encode('utf-8')) # send the final value to the server
    file.close() # closes the file
    response = client.recv(1024).decode('utf-8') # recieve response from server and decode
    print("Response:", response) # print response
    log_event(response, file_name, "Uploading file")  # Logs what happened on the user side (If uploading worked or not)



                                                             
'''-----------------------------------------------------------------------------------------------------------------------------------------------------  
--------------------------------------------------------------------------------------------------------------------------------------------------------'''     



# Written by: Makram El Hadi                                                       
def download_files():
    conn = sqlite3.connect(str(log_file_path / "Logs.db")) # connect to database
    cursor = conn.cursor() # connection between code and database

    arrOfFiles = client.recv(1024).decode('utf-8') # receives list of files
    print(arrOfFiles) # prints the list

         
    file_name = input("Enter the file name you would like to download: ").strip(' &"\'') # asks the client what file they would like to download
    client.send(file_name.encode('utf-8')) # sends file name (to download) to the server

    response = client.recv(1024).decode('utf-8')
    print(response)
    if response == "Entered file does not exist, maybe try again": # checks if response is valid and chooses accordingly what to do
        return

    result = client.recv(1024) # recieves file_size and file_id from the server
    list = result.split(b'\n') # splits the result to get each seperately

    file_size = int(list[0].decode('utf-8')) # unpacks file_size from result
    file_id = int(list[1].decode('utf-8')) # unpacks file_id from result
    
    while True:

        directory = input("Enter the path where you want to download file : ").strip(' &"\'') # Get the directory 
                                                                                    # directly from the user
                                                                                    # use the .strip() to remove any 
                                                                                    # spaces, the and(&) character,
                                                                                    #  both the single and double
                                                                                    #  quotation at the start and the 
                                                                                    # end of the string

        directory = os.path.join(os.path.expanduser("~"), directory) # makes sure that the directory specified is an absolte path (C:\User..)                                                                   
        directory = os.path.abspath(directory) # makes sure that the directory is an absolute path (in case it wasn't C:\User...)

        user_dir = Path(directory)  # specifies that the input receieved from the user is actually a path

        if user_dir.is_dir() == True: # if the directory is a valid directory and exists we continue the code normally
            break
        else: # we go back to the start of the loop and prompt the user again.
            print("Invalid directory. Please try again. \n")

                                                                           

    user_dir.mkdir(parents=True, exist_ok=True) # checks wether the file we want to create already exists or not

    file_path = user_dir/file_name # initializes the file path where we will write/download the file there.

    og_name = file_name # saves name in case needed later
    og_size = file_size # saves size in case needed later
    og_path = file_path # saves path in case needed later


    while file_path.exists(): # checks if file already exists in directory || If yes we enter the loop
            
            cursor.execute("SELECT file_id, last_received_byte FROM files_info WHERE file_name = ?", (file_name,))
            row = cursor.fetchone() # gets the file_id and last_received_byte from the databse to check wether that file
                                    # needs to be resumed or downloaded as a new file.
            
            if row is not None: # if file exists in directory and in the database 

                file_id_db = row[0] # gets the file_id of a file with the same name stored in database (used to compare)
                last_received_byte_db = row[1] # gets the last_received_byte to know where to continue from 

                #print("last_received_byte: ", last_received_byte_db) # these two lines not necesary for debugging purposes
                #print("og size: ", og_size)


                if file_id_db == file_id and last_received_byte_db < og_size: # checks if the file being downloaded has been downloaded
                                                                              # before or exists before using file_id as an identifier. 
                                                                              # Also checks if the size of the file that already exists
                                                                              # is less than the size of the file currently being
                                                                              # downloaded. If yes, resume download.
                                 
                    last_received_byte = last_received_byte_db # sets last_received_byte value to it's correct value from 
                                                               # databse (Updated in the loop)

                    print("Resuming download") # prints that it's resuming downloads
                    mode = "rb+" # specifies the mode to be read + write binary where
                                 # it opens an existing file for reading and writing in binary mode.The file must already exist.
                    break

                else: # file exsists in directory and in database and previously was fully downloaded
                      # last_received_byte_db == file_size.
                    print("File already exists! ") # moves to prompt the user to Save as new file or Replace
            else: # file exists in directory, but not in database
                print("File already exists in directory, but not found in the database ")

            # in all cases other than the same file_id and last_received_byte < og_size there will be a prompt for the user 
            # to either Save the file as a new file or to Replace(overwrite) the file

            last_received_byte = 0 # in this case we are starting from the beginning so last_received_byte initialized to 0
            mode = "wb"            # mode initialized to write binary


            user_input = input("Would you like to Save as new file(1) or Replace(2)? ").strip() # asks user to Save as a new file(1)
                                                                                                    # (similar to Rename) or to overwrite(2)  

            while(not user_input.isdigit() or int(user_input) not in [1,2]): # keeps looping until user_input is 
                                                                             # valid (checks is user_input is a
                                                                             # digit and if that digit is either
                                                                             # 1 or 2, if not it prompts again)
                
                print("Invalid Input! Please try again ")
                user_input = input("Would you like to Save as new file(1) or Replace(2)? ").strip() # prompts again

            user_input = int(user_input) # turn the string user input into an int

            if user_input == 1: # Save as new file

                extensions = file_path.suffixes # gets the extension(s) of the file
                    
                new_file_name_woExt = input("Enter new file name: ").strip() # takes in new file name
                new_file_name_wExt = new_file_name_woExt +''.join(extensions) # joins the new file name with the extensions of the og file
                file_name = new_file_name_wExt

                print("New File Name: ", file_name)
                file_path = user_dir/file_name # updates the file path to support the new file name
                file_size = og_size # saves file size as the original file size

            else: # if user chooses to overwrite(2)
                cursor.execute("""
                        INSERT OR REPLACE INTO files_info (file_name, file_size, file_id, last_received_byte)
                        VALUES (?, ?, ?, ?)
                        """, (file_name, file_size, file_id, 0)) # reintialize last_received_byte to 0 because
                                                                    # we will consider it to be new download
                conn.commit()

                break # exit the loop ("wb" mode automatically overwrites the file)

    else: # this is the case where the file is completely new, wether in database or not doesn't matter. The file doesn't exist in the 
          # database
           
        last_received_byte = 0 # in this case we are starting from the beginning so last_received_byte initialized to 0
        mode = "wb" # mode initialized to write binary

    client.send(str(last_received_byte).encode('utf-8')) # sends last_received_byte to the server so that it knows from where to start 
                                                         # sending the remaining chunks

    cursor.execute("""INSERT INTO files_info (file_name, file_size, file_id, last_received_byte) 
                        VALUES (?, ?, ?, ?)""", 
                            (file_name, file_size, file_id, last_received_byte))
    
    conn.commit() # Inserts into the database the file_name, file_id and last_received_byte into databse in order to track which
                  # bytes were received


    sha_256 = hashlib.sha256() # initializes hash function
    file = open(file_path, mode) # open the file in the specifed mode
    file.seek(last_received_byte) # tells the file to go to the last_received_byte in order to continue downloading from there 
                                  # (matters only to resume downloads because last_received_byte is initialized to last_received_byte_db) 
                                  # (in all other cases last_received_byte is 0)

    received_data = last_received_byte # initializes the amount of received data from the server

    commit_threshold = 1024 * 1024 * 100 # 100 MB || This is used to make the code faster and reliable (to not commit into the database
                                         # after every packet/chunk is received becasue that would create overhead and the code would run
                                         # really slow. So we commit into the database every 100 MegaBytes (MB))

    last_commit_point = received_data # keep track of the last time we commited into the database. Initialized to last_receieved_byte 
                                      # (matters only to resume downloads because last_received_byte is initialized to last_received_byte_db) 
                                      # (in all other cases last_received_byte is 0)
    master = Tk() # initialize progress bar
    master.title(f"Downloading {file_name}")
    prog = Progressbar(master,
                       orient=HORIZONTAL,
                       length=300,
                       mode='determinate',
                       maximum=file_size)  #give parameters like title and pixel length
    prog.pack(padx=10, pady=10)
    
    while received_data < file_size:  # keeps going untill full file is recieved

        packet = client.recv(min(1024, file_size - received_data)) # if file is almost done then file_size - received_data would be less
                                                                   # than the TCP socket buffer size, which is why we always take the min
                                                                   # between them

        sha_256.update(packet) # updates the hashing function
        file.write(packet) # writes the packet to the file 
        received_data = received_data + len(packet) # updates the amount of received packets
        prog['value'] = received_data #set progress bar to recieved data
        master.update() #update progress bar

        cursor.execute ("UPDATE files_info SET last_received_byte = ? WHERE file_name = ?", (received_data, file_name)) # Updates the value
                                                                                                                        # of last_received_byte
                                                                                                                        # into the database after 
                                                                                                                        # each iteration so that
                                                                                                                        # later on we can resume
                                                                                                                        # from last place we stopped
                                                                                                                        # at. 

        if received_data - last_commit_point >= commit_threshold: # checks the window to commit into the database

            conn.commit() # Updates the value of last_received_byte to keep track of which chunk has been downloaded
            last_commit_point = received_data # updates the last_commit_point so we know when to commit next
    master.destroy() # remove window of progress bar 
    file.close() 
    serverhash = client.recv(1024).decode('utf-8') # receives the hash from the server
    # ack = client.send("Hash received".encode('utf-8')) # sends ack to the server that the hash was received
    client.send("Hash received".encode('utf-8')) # sends ack to the server that the hash was received
    clienthash = sha_256.hexdigest() # computes the hash we updated in the loop

    if serverhash != clienthash: # checks wether the client and server hashes are identical 
        print("Error: File hashes do not match!") # they are not identical 
        result = "Error: File hashes do not match!" # saves result for logging
        os.remove(file_path)  # we delete it from the directory it is stored in
        cursor.execute("DELETE FROM files_info WHERE file_name = ?", (file_name,))
    else:
        print("File downloaded") # they are identical 
        result = "File downloaded" # saves result for logging
    local_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
            INSERT OR REPLACE INTO files_info (file_name, file_id, upload_date, file_size, last_received_byte, client_hash)
            VALUES (?, ?, ?, ?, ?, ?) """, (file_name, file_id, local_time, file_size, received_data, clienthash))
    conn.commit() # Inserts or replaces all needed data into the databse. 
    conn.close() # closes connection with database

    log_event(result , file_name, "Downloading file" ) # logs event 
    return
   

# Written by: Hassan Takruri  
def delete():

    x = client.recv(1024).decode('utf-8')  # recieve the list of files

    print(x)  # print the list
    file_name = input(str("Enter the file name you would like to delete: ")) # take input of the file name 
    client.send(file_name.encode('utf-8')) # send file name to the server
    result = client.recv(1024).decode('utf-8') # get the result message (error or success)
    print(result) # print result 
    log_event(result , file_name, "Deleted file" ) # logs the result of the procedure
    return


# Written by: Joseph Chahine
def save_logs():
    try:
        ack = "Ready to receive"
        client.send(ack.encode('utf-8'))  # Step 0: Let the server know the client is ready to receive logs

        # Step 1: Receive total size of log data
        size_str = client.recv(1024).decode('utf-8')  # Get the size of the logs file from the server
        ack = "Received size"
        client.send(ack.encode('utf-8'))  # Confirm to server that size was received

        if size_str.startswith("No logs available."):  # If server says there's nothing to send
            print(size_str)  # Just display the message
            return  # Exit the function

        total_size = int(size_str)  # Convert the size string to an integer
        print(f"[+] Total log size to receive: {total_size} bytes")  # Log total size for feedback

        # Step 2: Ask user where to save the logs
        save_path = input("Enter the folder path where you want to save the logs: ").strip(' &"\'')  
        # Clean input to avoid path issues

        if not os.path.exists(save_path):  # If folder doesn't exist
            print("Path does not exist.")  # Inform the user
            log_event("PATH DOES NOT EXIST", "NONE", "LOGS")  # Log the issue
            return  # Exit function

        # Step 3: Receive log data in chunks
        received_data = 0  # Start with no data received
        log_data = b""  # Bytes object to hold all received chunks

        while received_data < total_size:  # Keep receiving until we get all bytes
            packet = client.recv(min(1024, total_size - received_data))  # Read in chunks of 1024 or less (last chunk)
            if not packet:
                break  # Stop if nothing was received (unexpected)
            log_data += packet  # Append to log_data
            received_data += len(packet)  # Update how much we’ve received

        # Step 4: Decode and save logs
        decoded_logs = log_data.decode('utf-8')  # Convert bytes to string
        full_path = os.path.join(save_path, "server_logs.txt")  # Set full path to save the logs

        with open(full_path, "w") as f:
            f.write(decoded_logs)  # Write the logs to a file

        print(f"Logs saved to {full_path}")  # Confirmation message
        log_event("LOGS Fetched", "NONE", "LOGS")  # Log that logs were saved successfully
        return

    except Exception as e:
        print("Error receiving logs:", e)  # Print error message
        log_event(f"ERROR: {e}", "NONE", "LOGS")  # Log the error

#Written by: Joseph Chahine
def handle_client(message):
    user_input = input("Enter username and password: ")  # Prompt the user to enter credentials (username + password)

    client.send(user_input.encode('utf-8'))  # Send those credentials to the server
    response = client.recv(1024).decode('utf-8')  # Get server's response (success or failure)
    print(response)  # Display the response to the user

    # LOGIN Case 
    if message.upper() == "LOGIN" and response[0:12] != "Welcome back":
        # If login failed (doesn't begin with "Welcome back"), log the failure
        log_event(response, "None", "LOGIN")
        client.close()  # Close connection to server
        exit()  # Exit the program

    #CREATE Case
    while message.upper() == "CREATE" and response[0:28] != "Account created successfully":
        # Loop until the user provides a valid (new) username
        if response[0:13] == "Invalid input":
            # If input format is wrong (missing username/password), log it and exit
            log_event("Invalid input", "None", "CREATE")
            client.close()
            exit()

        user_input = input("Enter a different username and password seperated by a space: ")
        client.send(user_input.encode('utf-8'))  # Send the new credentials
        response = client.recv(1024).decode('utf-8')  # Receive server's feedback
        print(response)

    # Log successful CREATE or LOGIN
    log_event(response, "None", message.upper())

    
    response = client.recv(1024).decode('utf-8')  # Receive operation menu / prompt
    print(response)
    user_input = input("Enter opertaion: ")
    client.send(user_input.encode('utf-8'))  # Send desired operation
    response = client.recv(1024).decode('utf-8')  # Server acknowledges or responds to request
    print(response)

   
    while user_input.upper() != "DISCONNECT":  # Keeps asking user for inputs as long as they dont disconnect

        if response == "Ready to recieve file" and user_input.upper() == "UPLOAD":
            upload_files()  # Run upload function
        elif response == "List of Files: " and user_input.upper() == "LIST":
            arrOfFiles = client.recv(1024).decode('utf-8')  # Get list of files
            print(arrOfFiles)
            log_event("List of files", "None", "List")  # Log this event
        elif response == "Which file would you like to download " and user_input.upper() == "DOWNLOAD":
            download_files()  # Run download function
        elif response == "what do you wish to delete" and user_input.upper() == "DELETE":
            delete()  # Run delete function
        elif response == "SERVER RESPONSE:LOGS ready to be sent" and user_input.upper() == "LOGS":
            save_logs()  # Admin request to fetch logs
        elif response == "operation not available":
            break  # Exit loop if server doesn't allow operation or it doesnt exist

        response = client.recv(1024).decode('utf-8')  # Get new prompt/response from server
        print(response)
        user_input = input("Enter your next operation:")  # Ask for the next command
        client.send(user_input.encode('utf-8'))  # Send it
        response = client.recv(1024).decode('utf-8')  # Server responds again
        print(response)

        if response == "operation not available":
            break  # Exit loop if invalid input

    log_event(response, "NONE", "DISCONNECTED")  # Log disconnect event

            


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((socket.gethostbyname(socket.gethostname()), 9999))

# Receive and print the first message from the server
response = client.recv(1024).decode('utf-8')
print(response)
# Send first response (CREATE or LOGIN)
message = input("Write here: ").strip()
client.send(message.encode('utf-8'))
response = client.recv(1024).decode('utf-8')
print(response)  # Server asks for username and password

# Receive and print the second message from the server (only if user chose CREATE)
if message.upper() =="LOGIN" or message.upper()=="CREATE":
    handle_client(message)
else:
    log_event("Invalid choice","None","Authentication")
client.close()
