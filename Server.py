import socket
import threading
from datetime import datetime
from pathlib import Path
import sqlite3
import hashlib
import random
import os


# Change BASE_ DIR to custom path
BASE_DIR = Path(r"")
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # creating stream socket

server.bind((socket.gethostbyname(socket.gethostname()), 9999))  # binding the server

# Written by: Joseph Chahine
def log_event(user_id, event_type, event_details):  # Function to insert a log entry into the logs table
    conn = sqlite3.connect("files.db")  # Connect to the SQLite database named 'files.db'
    cursor = conn.cursor()  # Create a cursor to execute SQL commands

    local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get the current timestamp in a readable format

    # Create formatted log message
    formatted_log = (
        f"\n"
        f"[{local_time}]\n"                    # Timestamp of when the event occurred
        f"User ID:    {user_id}\n"             # ID of the user who triggered the event
        f"Event:      {event_type}\n"          # Type of event ( LOGIN, CREATE, UPLOAD...)
        f"Details:    {event_details}\n"       # More specific information about the event
        f"----------------------------------------\n"  # Separator for readability
    )

    # Insert the formatted log into the logs table
    cursor.execute("""
        INSERT INTO logs (formatted_msg)
        VALUES (?)
    """, (formatted_log,))  # Use parameterized SQL to safely insert the log message

    conn.commit()  # Save changes to the database
    conn.close()   # Close the database connection

# Written by: Joseph Chahine
def setup_database():
    conn = sqlite3.connect("files.db")  # Connect to (or create) a SQLite database named 'files.db'
    cursor = conn.cursor()  # Create a cursor object to execute SQL commands

    # Create 'users' table if it doesn't already exist
    cursor.execute("""CREATE TABLE IF NOT EXISTS users( 
        user_id INTEGER PRIMARY KEY,                
        username TEXT NOT NULL UNIQUE,             
        password TEXT NOT NULL                     
    );""")
    #Unique ID for each user,Username must be unique and not null,Password which can't be NULL

    # Create 'files_info' table to store uploaded file metadata
    cursor.execute("""CREATE TABLE IF NOT EXISTS files_info(
        file_id INTEGER PRIMARY KEY,               -- Unique ID for each file
        file_name TEXT NOT NULL,                   -- Name of the file (not null)
        owner_id INTEGER NOT NULL,                 -- ID of the user who owns the file (foreign key)
        current_version INTEGER DEFAULT 1,         -- File version, default starts at 1
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Timestamp of when file was uploaded
        file_path TEXT NOT NULL,                   -- Path where the file is stored on disk
        size INTEGER NOT NULL,                     -- Size of the file in bytes
        checksum TEXT NOT NULL,                    -- SHA-256 hash of the file for integrity check
        FOREIGN KEY(owner_id) REFERENCES users(user_id)   -- owner_id must exist in the users table
    );""")
    #Unique ID for each file,Name of the file (not null),ID of the user who owns the file (foreign key),File version, default starts at 1
    #Timestamp of when file was uploaded

    # Create 'logs' table to store formatted log entries
    cursor.execute("""CREATE TABLE IF NOT EXISTS logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,  
        formatted_msg TEXT                         
    );""")
    #Auto-incremented unique ID for each log,Full formatted message string

    conn.commit()  # Save (commit) all changes to the database
    conn.close()   # Close the connection to the database


setup_database()
#setup admin written by : Hassan Takruri
conn = sqlite3.connect("files.db")  #connect to database
cursor = conn.cursor()
cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (100000,)) # here we are checking if this id is taken, if it isnt, we create the admin with this id
result = cursor.fetchone()  # Check if the ID exists
hashed_password = hashlib.sha256("admin".encode()).hexdigest()   # we hash the admin's password
if result is None:  # id is not used, we give it to admin

    cursor.execute("""INSERT INTO users (user_id, username, password) 
                        VALUES (?, ?, ?)""", 
                            (100000, "admin", hashed_password, )) #insert in the users database the info of admin
    conn.commit()
    user_dir = BASE_DIR / "admin"    # create  a  directory for admin
    user_dir.mkdir(parents=True, exist_ok=True)
## if the id 100000 is used, it means admin was already initialized and exists
# this code basically means create admin if he doesnt exist

# Written by: Joseph Chahine
def generateuserID():
    conn = sqlite3.connect("files.db")  # Connect to the database
    cursor = conn.cursor()

    while True:
        user_id = random.randint(100000, 999999)  # Generate a random 6-digit ID
        
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()  # Check if the ID exists

        if result is None:  # If the ID is not in the table, return it
            conn.close()
            
            return user_id

# Written by: Hassan Takruri 
def generatefileID():
    conn = sqlite3.connect("files.db")  # Connect to the database
    cursor = conn.cursor()

    while True: #infinite loop till we get  a unique file id
        file_id = random.randint(100000, 999999)  # Generate a random 6-digit ID
        
        cursor.execute("SELECT file_id FROM files_info WHERE file_id = ?", (file_id,))
        result = cursor.fetchone()  # Check if the ID exists

        if result is None:  # If the ID is not in the table, return it
            conn.close()
            return file_id

# Written by: Hassan Takruri
# Help by: Makram El Hadi 
def send_file(connection, address, username):

    conn = sqlite3.connect("files.db")  # Connect to the database
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users WHERE username = ?", (str(username),)) # gets user ID to pass to list function 
    result = cursor.fetchone()
    user_id = result[0] # stores the ID in user_id

    x = list_files(user_id) # gets the list of files in database
    connection.send(str(x).encode('utf-8')) # sends the list of files to the client
    

    name = connection.recv(1024).decode('utf-8')   # get from the client the name of the file they require to download
    print("NAME OF THE FILE IS:",name) #server side print not needed

    cursor.execute("SELECT file_path FROM files_info WHERE file_name = ?", (str(name),))   # we search for this file's path from the database using the name that the client sent
    result = cursor.fetchone()
    

    if result is None: # if no result came from our search, then the sent file name does not match any file stored in our database, either the client requested an unavailable file, or misspelled one
        connection.send("Entered file does not exist, maybe try again".encode('utf-8')) # inform the client of the failure
        log_event(user_id,"DOWNLOAD","FAIL") # we log this as a failed download
        return
    else:
        # connection.send("Fetching File: ".encode('utf-8') + b'\n' + str(file_size).encode('utf-8') + b'\n') # tell the client that we are proceeding
        connection.send("Fetching File: ".encode('utf-8'))

    file_path = result[0] # since result is a tuple, we are extracting file_path 

    cursor.execute("SELECT size FROM files_info WHERE file_name = ?", (str(name),))  # searching for the size of the file so we may tell the client
    result1 = cursor.fetchone()

    file_size = int(result1[0])  # again result is a tuple so we need to extract file_size    

    cursor.execute("SELECT file_id FROM files_info WHERE file_name = ?", (str(name),)) # gets file_id from database for that specific file
    result = cursor.fetchone()
    file_id = int(result[0]) # unpack tuple and save file id

    connection.send(str(file_size).encode('utf-8')+ b'\n' + str(file_id).encode('utf-8') + b'\n') # send file_size 
                                                                                                  # and file_id with
                                                                                                  # delimeters



    file = open(file_path,"rb")  # open the file in read bytes mode

    last_received_byte = int(connection.recv(1024).decode('utf-8')) # gets last_received_byte from client so that the server knows
                                                                    # from where to start sending packets wether it's to resume a download
                                                                    # or to start a new one.

    file.seek(last_received_byte) # adjust file pointer position to actaully start the last received byte

    sentdata = last_received_byte  # we will use this to keep track of how much data we have sent so far
    sha_256 = hashlib.sha256()  #hash object || actually performs the hashing algorithm based on the sha-256 way and gets updated
                               # using .update (used below)

    while sentdata < file_size:
        packet = file.read(min(1024,file_size - sentdata)) # will read 1024 bytes of data and then increment to the next chunk of data, however if less than 1024
                                                         # bytes are available, it will only raed that value of bytes
        
        connection.send(packet) #sends the packet to client
        sha_256.update(packet)   # will update the hash value based on the read data
        sentdata = sentdata + len(packet)  #updates the amount of data read after this iteration

    serverhash = sha_256.hexdigest() # returns the completed hash in hexaecimal format

    file.close()  # closes file
    connection.send(serverhash.encode('utf-8')) # sends the checksum to client so that they can check for errors after recieving
    print(connection.recv(1024).decode('utf-8')) # waits for ack
    log_event(user_id,"DOWNLOAD","SUCCESS")  # we log the success of this download
    conn.close() # closes connection with database

# Written by: Hassan Takruri 
def recv_file(connection,address,username):
    conn = sqlite3.connect("files.db")  # Connect to the database
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users WHERE username = ?", (str(username),)) # we find the id of the user based on his username from SQL tables
    result = cursor.fetchone()
    user_id = result[0] # unpack tuple and store user id in user_id
    
    user_dir = BASE_DIR / str(username) # create directory inside our main directory with name = username of client
    user_dir.mkdir(parents=True, exist_ok=True)   

    arr = connection.recv(2048) # recieve the file name and file size from the client bundled together

    list = arr.split(b'\n')   #split file name and file size
    file_name = list[0]   #save file name in file_name
    file_size = list[1]  # save file size in file_size
    file_name = file_name.decode('utf-8')   #decode into proper format

    plate_name = file_name # save the base name of file as plate name ; we do this since we might have to modify the name incase of versions
    
    cursor.execute("SELECT MAX(current_version) FROM files_info WHERE file_name LIKE ?", (f"%{plate_name}%",)) # searches for the newest version of the file
    result = cursor.fetchone()
    v = result[0] or 0   # this variable is 0 if there is no other version, else it is the value of the version
    
    current_version = v+1 # define the version of the file - if v was 0, it becomes 1 and is the 1st version- but if v = n, becomes n+1 and is the (n+1)th version
    
       
        
    if v> 0 : # check if v is not 0, if not then there are versions of the file, so we adopt the below format
        file_name = str("v_"+str(v+1)+str(plate_name)) # the name becomes v_current version + base name of file
   
   
   
    file_size = int(file_size.decode('utf-8')) # make the recieved file size an int
    
    file_path = user_dir/file_name  # inside our client directory , we create a new sub path title  with name of file
    
    print("File Path:", file_path)  # server side print not needed
    file_id = generatefileID()  # give this file a unique file id using the generate file id function
    print("File ID:", file_id)  # server side print not needed
    sha_256 = hashlib.sha256()  # this initializes our hash checksum of format sha256
    file = open(file_path, "wb")  # we open a file in the designated file path defined above in write bytes mode so we may begin recieving data
    received_data = 0 # initialize recieved data to 0 so we can track how far along we are

    while received_data < file_size:  # keep on recieving untill full file is delivered
        packet = connection.recv(min(1024, file_size - received_data))  # will read 1024 bytes of data and then increment to the next chunk of data, however if less than 1024
                                                         # bytes are available, it will only raed that value of bytes
        file.write(packet)  # write the data in the file
        sha_256.update(packet)  # add the hash of this packet to our rolling checksum
        received_data = received_data+len(packet) # update

    client_checksum = connection.recv(1024).decode('utf-8') # get checksum from client
    checksum = sha_256.hexdigest() # define our checksum as checksum

    if checksum != client_checksum: # if checksums are not equal between client and server then the file has been corrupted
        connection.send(str("Error").encode('utf-8')) #we tell the client the upload encountered error
        os.remove(file_path)  # we delete it from the directory it is stored in
        cursor.execute("DELETE FROM files_info WHERE file_name = ?", (file_name,))#delete from database
        log_event(user_id,"UPLOAD","ERROR") # we log the failed upload
        return
    else :
        connection.send(str("Success").encode('utf-8')) # tell the client that upload was successful
    

    conn = sqlite3.connect("files.db")  # Connect to the database
    cursor = conn.cursor() 
    local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  #define time now as local_time

    cursor.execute("""INSERT INTO files_info (file_id, file_name, owner_id, current_version, upload_date, file_path, size, checksum) 
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                        (file_id, file_name, user_id, current_version,local_time, str(file_path), file_size, checksum )) #insert all the file info into the database
    conn.commit()
    log_event(user_id,"UPLOAD","SUCCESS") # we log a successful upload
    conn.close()


# Written by: Joseph Chahine
# Help by: Makram El Hadi
def list_files(user_id):
    conn = sqlite3.connect("files.db")
    cur  = conn.cursor()

    # 1) join files_info → users to get file_name, username and upload_date
    cur.execute(
        "SELECT f.file_name, u.username, f.upload_date "
        "FROM files_info AS f "
        "JOIN users      AS u ON f.owner_id = u.user_id" #we join them on the condition that owner ID=userID, so that we know who uploaded what
    )

    rows = cur.fetchall()
    conn.close()

    # 2) log the event
    log_event(user_id, "LIST", "SUCCESS")

    # 3) build and return the list
    result = []
    for file_name, username, upload_date in rows:
        result.append(
            f"\nFile Name: {file_name}\nUsername: {username}\nUpload Date: {upload_date}\n" #add string to a list which we will send to user
        )
    if len(result)!=0:
        return ''.join(result) 
    else:
        return result


# Written by: Hassan Takruri 
# Help by: Joseph Chahine
def request(connection,address,username,ID):   
    connection.send("Would you like to : \nUpload file(enter UPLOAD) \nDownload file(enter DOWNLOAD) \nList of files(enter LIST) \nDisconnect(enter DISCONNECT)".encode('utf-8'))  # when request gets called it asks the user what operation they would like to do

    inp = connection.recv(1024).decode('utf-8').upper()   # gets input from user, makes it capital so we can match to options 
    if inp not in [ "UPLOAD", "DOWNLOAD","LIST","DISCONNECT"]:  # if the input is not a defined function then we inform the client and disconnect
        connection.send("operation not available".encode('utf-8'))
        log_event(ID,"OPERATION","UNAVAILABLE") # we log the undefined operation
        return
    while inp!="DISCONNECT":  # as long as the client does not choose to disconnect, then we keep requesting his input on what to do
        if inp == "UPLOAD":
            connection.send("Ready to recieve file".encode('utf-8'))  # if input is upload , we initiate the upload sequence by calling recv
            recv_file(connection,address,username)
        elif inp == "LIST": 
            connection.send("List of Files: ".encode('utf-8'))  # if inout is list, we comput the list of files using our function
            x = list_files(ID)
            connection.send(str(x).encode('utf-8')) # we send the compute list of files
        elif inp=="DOWNLOAD":
             connection.send("Which file would you like to download ".encode('utf-8')) # if input is download we initiat ethe download sequence by calling send

             send_file(connection, address, username) # call send files
        
        connection.send("What would you like to do next: \nUpload file(enter UPLOAD) \nDownload file(enter DOWNLAOD) \nList of files(enter LIST) \nDisconnect(enter DISCONNECT)".encode('utf-8'))  # we again ask the client what they would like to do so that we may update loop condition
        inp = connection.recv(1024).decode('utf-8').upper()
        if inp not in [ "UPLOAD", "DOWNLOAD","LIST","DISCONNECT"]:  # if user input is not a defined function then we disconnect
            connection.send("operation not available".encode('utf-8'))
            log_event(ID,"INPUT","INVALID")# log the undefined request
            return

    connection.send("DISCONNECTING".encode('utf-8'))#when inp==DISCONNECT we will exit the while loop and disconnect,connection.close() happens in the calling function
    log_event(ID,"DISCONNECTING","SUCCESS")#after exiting the loop we will store DISCONNECT in the log table.
    return

# Written by: Hassan Takruri 
def deletefile(connection,address,username):
    conn = sqlite3.connect("files.db")  # Connect to the database
    cursor = conn.cursor()
    x = list_files(100000) # we send the admin a list of file so that they may choose what to delete
    connection.send(str(x).encode('utf-8')) # sending list
    name = connection.recv(1024).decode('utf-8') # get name of file from the client
    cursor.execute("SELECT file_path FROM files_info WHERE file_name = ?", (str(name),))   # we search for this file's path from the database using the name that the client sent
    result = cursor.fetchone()  
    if result is None: # if there is no file path for that file, then it does not exist 
        connection.send("file not found".encode('utf-8')) # we tell the client taht the file was not found
        log_event(100000, "DELETE", "FAIL")  # we log the failed delete
    else:  # if file path exists
        file_path = result[0]
        os.remove(file_path)  # we delete it from the directory it is stored in
        cursor.execute("DELETE FROM files_info WHERE file_name = ?", (name,))  # remove the file from the database 
        connection.send("completed".encode('utf-8'))  # send the success message to the client
        conn.commit() # save the changes to the database
        log_event(100000, "DELETE", "SUCCESS") # log the success
    return

# Written by: Joseph Chahine
def send_log_files(conn):
    try:
        # Connect to the SQLite database where logs are stored
        db_conn = sqlite3.connect("files.db") 
        cursor = db_conn.cursor()  # Create a cursor to interact with the database

        # Execute SQL query to fetch all formatted logs from the 'logs' table
        cursor.execute("SELECT formatted_msg FROM logs")
        logs = cursor.fetchall()  # Fetch all results (as a list of tuples)

        if not logs:  # If the logs list is empty
            conn.send("No logs available.".encode('utf-8'))  # Send message that there are no logs
        else:
            # Inform client that logs are ready to be sent
            conn.send("SERVER RESPONSE:LOGS ready to be sent".encode('utf-8'))  
            
            ack = conn.recv(1024).decode('utf-8')  # Wait for acknowledgment from the client
            if ack:
                print("Client ready to receive logs")  #print

            # Combine all log entries into a single string with line breaks
            all_logs = "\n".join(row[0] for row in logs)  
            log_bytes = all_logs.encode('utf-8')  # Encode the log string to bytes for transmission

            total_size = len(log_bytes)  # Calculate total size in bytes of the log data
            conn.send(str(total_size).encode('utf-8'))  # Send the size to the client

            ack = conn.recv(1024).decode('utf-8')  # Wait for client to acknowledge  size
            if ack:
                print("Client received file size")  # print

            # Initialize how many bytes have been sent so far
            sent_data = 0
            while sent_data < total_size:  # Continue sending until all bytes are sent
                chunk_size = min(1024, total_size - sent_data)  # Choose the smaller of 1024 or remaining data
                chunk = log_bytes[sent_data:sent_data + chunk_size]  # takes the chunk that we want to send and saves it in variable
                conn.send(chunk)  # Send the chunk
                sent_data += len(chunk)  # Update total sent bytes

            # Log successful log sending in the database
            log_event("100000", "Fetching logs", "Success")

        db_conn.close()  # Close the database connection

    except Exception as e:  # If an error occurs at any point
        error_msg = f"Error retrieving logs: {e}"  # Create an error message
        conn.send(error_msg.encode('utf-8'))  # Send error message to client

        if 'db_conn' in locals():  # Check if db_conn exists in the current scope
            db_conn.close()  # Close database connection

        # Log the failure of the operation
        log_event("100000", "Fetching logs", "Fail")


# Written by: Hassan Takruri 
def requestadmin(connection,address,username,ID):
    connection.send("What would you like to do: \nUpload file(enter UPLOAD) \nDownload file(enter DOWNLAOD) \nList of files(enter LIST) \nDelete (enter DELETE) \nLogs of files(enter LOGS)\nDisconnect(enter DISCONNECT)".encode('utf-8')) # when requestadmin gets called it asks the admin what operation they would like to do
    inp = connection.recv(1024).decode('utf-8').upper() # gets input from user, makes it capital so we can match to options 
    if inp not in [ "UPLOAD", "DOWNLOAD","LIST","DISCONNECT","DELETE","LOGS"]: # if the input is not a defined function then we inform the client and disconnect
        connection.send("operation not available".encode('utf-8'))
        log_event(ID,"INPUT","INVALID") # we log the undefined operation
        return
    while inp!="DISCONNECT": # as long as the client does not choose to disconnect, then we keep requesting his input on what to do
        if inp == "UPLOAD":
            connection.send("Ready to recieve file".encode('utf-8')) # if input is upload , we initiate the upload sequence by calling recv
            recv_file(connection,address,username)

        elif inp == "LIST":
            connection.send("List of Files: ".encode('utf-8')) # if inout is list, we comput the list of files using our function
            x = list_files(ID)
            connection.send(str(x).encode('utf-8')) # we send the compute list of files

        elif inp=="DOWNLOAD":
             connection.send("Which file would you like to download ".encode('utf-8')) # if input is download we initiat ethe download sequence by calling send

             send_file(connection, address, username) # call send files

        elif inp == "DELETE": # if the admin input is delete , we initiate the file deletion procedure by calling delete
            connection.send("what do you wish to delete".encode('utf-8'))
            deletefile(connection,address,username) # call delete
        
        elif inp=="LOGS": # if the admin input is logs, then we initiate the sending server logs procedure by calling send_log_files
            send_log_files(connection)

        connection.send("What would you like to do next: \nUpload file(enter UPLOAD) \nDownload file(enter DOWNLAOD) \nList of files(enter LIST) \nDelete (enter DELETE) \nLogs of files(enter LOGS)\nDisconnect(enter DISCONNECT)".encode('utf-8'))   # we again ask the client what they would like to do so that we may update loop condition
        inp = connection.recv(1024).decode('utf-8').upper()
        if inp not in [ "UPLOAD", "DOWNLOAD","LIST","DISCONNECT","DELETE","LOGS"]: # if user input is not a defined function then we disconnect
            connection.send("operation not available".encode('utf-8'))
            log_event(ID,"INPUT","INVALID") # log the undefined request
            return

    connection.send("DISCONNECTING".encode('utf-8'))#when inp==DISCONNECT we will exit the while loop and disconnect,connection.close() happens in the calling function
    log_event(ID,"DISCONNECTING","SUCCESS")#after exiting the loop we will store DISCONNECT in the log table.
    return

# Written by: Joseph Chahine
def handle_client(connection, address):
    connection.send("Welcome! Do you wish to create a new account or log into your existing account? Write CREATE or LOGIN".encode('utf-8'))  # Ask client to choose CREATE or LOGIN
    
    msg1 = connection.recv(1024).decode('utf-8').strip().upper()  # Receive action, strip spaces, convert to uppercase
    if msg1 not in ["CREATE", "LOGIN"]:  # If not a valid choice
        connection.send("Invalid choice. Disconnecting.".encode('utf-8'))  # Notify and close the connection
        connection.close()
        log_event("?", "INPUT", "INVALID FORMAT")  # Log the invalid attempt
        print("Invalid input,closing connection")  #Print to terminal just for more clarity 
        return
    
    connection.send("Please type in your username and password separated by a space".encode('utf-8'))  # After receiving msg of either create or login
    # we ask the user to enter username and password, to create an account or to look it up in our database
    
    msg2 = connection.recv(1024).decode('utf-8')  # Receive username and password
    print(f"Received from client: {msg2}")  # Print received credentials

    try:
        username, password = msg2.split()  # Try splitting the input into username and password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()  # Hash the password using SHA-256
    except ValueError:  # If input isn't two words
        connection.send("Invalid input format! Please enter both username and password separated by a space.".encode('utf-8'))  # Error message
        connection.close()
        log_event("?", "INPUT", "INVALID FORMAT")  # Log issue
        return

    conn = sqlite3.connect("files.db")  # Connect to the database
    cursor = conn.cursor()  # Create cursor 

    if msg1 == "CREATE":  # If user chose to create an account
        ID = generateuserID()  # Generate unique user ID
        while True:
            try:
                cursor.execute("INSERT INTO users (user_id, username, password) VALUES (?, ?, ?)", (ID, username, hashed_password))  # Try to insert new user
                conn.commit()  # Save to database
                connection.send(f"Account created successfully! Your user ID is {ID}".encode('utf-8'))  # Notify success
                log_event(ID, "CREATE", "SUCCESS")  # Log creation
                break  # Exit retry loop
            except sqlite3.IntegrityError:  # If username already exists, we tell the client and ask him to pick again. As long as he keeps picking
                                            #already existing usernames we keep on asking him
                print("username used")  # print in terminal for clarity
                connection.send(f"Error: Username '{username}' already exists. Please choose another.".encode('utf-8'))  # Prompt retry
                msg2 = connection.recv(1024).decode('utf-8')  # Receive new credentials
                try:
                    username, password = msg2.split()  # Try to split again, if username is used again we repeat process
                    hashed_password = hashlib.sha256(password.encode()).hexdigest()  # Rehash new password
                    print("The new username received is:", username)  # Debug print
                except ValueError:  # If input format invalid
                    print("Closing connection,invalid input")  #print in terminal we are closing connection
                    connection.send("Invalid input format! Disconnecting.".encode('utf-8'))  # Notify error
                    conn.close()
                    connection.close()
                    return
        
        conn.close()  # Close Data base connection
        request(connection, address, username, ID)  # Move to request handler (will handle user operations)

    elif msg1 == "LOGIN":  # If user chose to login
        cursor.execute("SELECT user_id FROM users WHERE username=? AND password=?", (username, hashed_password))  # Look up user
        result = cursor.fetchone()  # Get result

        if result is not None:  # If user found, we need to check it it's an admin or regular user
            if int(result[0] == 100000):  # If admin (ID == 100000)
                connection.send(f"Welcome back, {username}!".encode('utf-8'))  # Send greeting
                log_event(result[0], "LOGIN", "SUCCESS")  # Log admin login
                conn.close()
                requestadmin(connection, address, username, result[0])  # Call admin handler which has additional operations
            else:#regular user
                connection.send(f"Welcome back, {username}!".encode('utf-8'))  # Send greeting
                log_event(result[0], "LOGIN", "SUCCESS")  # Log user login
                conn.close()
                request(connection, address, username, result[0])  # Call user handler
        else:  # User not found
            connection.send("Account not found. Please check your credentials.".encode('utf-8'))  # Notify that account does not exist
            log_event("?", "LOGIN", "FAIL")  # Log failure
            conn.close()  # Close DB

    else:
        connection.send("Invalid input! Connection closed.".encode('utf-8'))  # any other case
        log_event("?", "INPUT", "INVALID")  # Log issue
        conn.close()

    connection.close()  # Close the socket connection



print("[Starting]")
server.listen()  # server listens for connections

while True:
    conn, addr = server.accept()  # accept request for connection, returns connection object and address of client
    print("Accepted connection")
    print("Connection established. Address of client", addr)
    thread = threading.Thread(target=handle_client, args=(conn, addr))
    thread.start()
