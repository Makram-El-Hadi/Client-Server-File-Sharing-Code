# Client-Server-File-Sharing-Code 

## Contributors

![Contributors](https://contrib.rocks/image?repo=Makram-El-Hadi/Client-Server-File-Sharing-Code)


1. Copy `server.py` and `client.py` into your working directory.
2. Modify `BASE_DIR` in `server.py` to point to a valid folder for file storage.
3. On the client machine, decide where logs should be stored (any writeable directory).

Running the Server 
------------------
1. Open a terminal in the server  directory.
2. Run: `python server.py`
3. The server will:
   - Initialize `files.db` with `users`, `files_info`, and `logs` tables.
   - Create an admin account (ID=100000, username=admin, password=admin) if not present.
   - Listen for connections on port 9999 (adjustable in code).

Running the Client
------------------
1. Open a terminal in the client directory.
2. Run: `python client.py`
3. At the prompt, enter the path for client logs (e.g., `C:\path\to\logs`).
4. Choose `CREATE` (new account) or `LOGIN` (existing credentials).
5. After authentication, follow prompts:
   - `UPLOAD`: Send a file—select path when prompted.
   - `DOWNLOAD`: Choose a file from the server’s list; supports resume.
   - `LIST`: View available files.
   - `DELETE`: (Admin only) Remove a file.
   - `LOGS`: (Admin only) Fetch server logs.
   - `DISCONNECT`: End session.





Commands & Detailed Workflow
----------------------------

### 1. UPLOAD
- Enter operation: `UPLOAD`
- Enter the file path you want to upload:` 
- Provide the absolute path (e.g., `C:\path\to\report.pdf`).
- Progress UI: A Tkinter window shows upload progress.
- Completion:  
  -
### 2. DOWNLOAD
- Enter operation: `DOWNLOAD`
- The client automatically prints the server’s file list.
- Enter the file name you would like to download:`  
  - Type the exact file name or versioned name (e.g., `v_2report.pdf`).
- Server response:Shows `Fetching File:` or error.
- Enter the path where you want to download file:  
  - Provide a path relative to your home directory or absolute.
- If file exists locally:  
  - Choose `1` to _Save as new file_ (then enter a new base name) or  
  - `2` to _Replace_ (overwrite).
- A Tkinter window shows download progress.
- Completion:

### 3. LIST
- Enter operation: `LIST`
- Output: Prints formatted list of all files (`File Name`, `Username`, `Upload Date`).
- No additional input required.

### 4. DELETE (Admin Only)
- Enter operation: `DELETE`
- server list: Prints list of files.
-`Enter the file name you would like to delete:`  
  - Type the exact file name.
- **Completion:**  

### 5. LOGS (Admin Only)
- Enter operation: `LOGS`
- Handshake: Client sends `Ready to receive`, server replies `LOGS ready to be sent`.
- Client Acknowledges: Sends `Received size` after size header.
- `Enter the folder path where you want to save the logs:`  
  - Choose a writable directory.
- **Completion:**  
  

### 6. DISCONNECT
- Enter operation: `DISCONNECT`
- **Completion:**  
  
