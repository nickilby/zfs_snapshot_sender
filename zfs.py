from flask import Flask, render_template_string, request
import pyperclip

app = Flask(__name__)

# HTML template for the form with enhanced CSS styling
form_template = '''
<!doctype html>
<html lang="en">
  <head>
    <title>ZFS Command Generator</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        margin: 50px;
        background-color: #f4f4f4;
      }
      h1 {
        color: #333;
        text-align: center;
      }
      form {
        background: #fff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        max-width: 500px;
        margin: auto;
      }
      label {
        display: block;
        margin-top: 15px;
        font-weight: bold;
        font-size: 16px;
        color: #555;
      }
      input[type="text"] {
        width: calc(100% - 22px); /* Full width minus padding and border */
        padding: 12px;
        margin: 5px 0 15px 0;
        border: 2px solid #007bff;
        border-radius: 5px;
        font-size: 14px;
        transition: border-color 0.3s;
      }
      input[type="text"]:focus {
        border-color: #0056b3;
        outline: none;
      }
      input[type="checkbox"] {
        margin: 10px 0;
        transform: scale(1.2); /* Enlarge the checkbox */
      }
      button {
        background-color: #007bff;
        color: white;
        padding: 12px 20px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-size: 16px;
        margin-top: 10px;
        transition: background-color 0.3s;
        width: 100%;
      }
      button:hover {
        background-color: #0056b3;
      }
      h2 {
        color: #333;
        text-align: center;
      }
      pre {
        background: #eee;
        padding: 10px;
        border-radius: 5px;
        overflow-x: auto;
        border: 1px solid #ccc;
      }
      .copy-button {
        background-color: #28a745;
        margin-top: 10px;
      }
      .copy-button:hover {
        background-color: #218838;
      }
    </style>
    <script>
      function copyToClipboard() {
        var commandText = document.getElementById("zfsCommand").innerText;
        navigator.clipboard.writeText(commandText).then(function() {
            showNotification("Command copied to clipboard!");
        }, function(err) {
            showNotification("Failed to copy command: " + err);
        });
      }

      function showNotification(message) {
        const notification = document.createElement("div");
        notification.innerText = message;
        notification.style.position = "fixed";
        notification.style.bottom = "20px";
        notification.style.right = "20px";
        notification.style.backgroundColor = "#28a745";
        notification.style.color = "white";
        notification.style.padding = "10px 15px";
        notification.style.borderRadius = "5px";
        notification.style.zIndex = "1000";
        notification.style.boxShadow = "0 2px 10px rgba(0,0,0,0.2)";
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000); // The notification will disappear after 3 seconds
      }
    </script>
  </head>
  <body>
    <h1>Generate ZFS Commands</h1>

    <form method="post">
      <label for="first_snapshot">First Incremental Snapshot:</label>
      <input type="text" name="first_snapshot" id="first_snapshot" required>

      <label for="last_snapshot">Last Incremental Snapshot:</label>
      <input type="text" name="last_snapshot" id="last_snapshot" required>

      <label for="destination_san">Destination SAN for Incrementals:</label>
      <input type="text" name="destination_san" id="destination_san" required>

      <label for="force_sync">Force Sync (-F): (Will Mirror Source) </label>
      <input type="checkbox" name="force_sync" id="force_sync">

      <button type="submit" name="action" value="incremental">Generate Incremental Command</button>
    </form>

    {% if incremental_command %}
    <h2>Generated Incremental Command:</h2>
    <pre id="zfsCommand">{{ incremental_command }}</pre>
    <button class="copy-button" onclick="copyToClipboard()">Copy Incremental Command</button>
    {% endif %}

    <form method="post" style="margin-top: 50px;">
      <label for="full_snapshot">Full Snapshot:</label>
      <input type="text" name="full_snapshot" id="full_snapshot" required>

      <label for="destination_full_san">Destination SAN for Full Snapshot:</label>
      <input type="text" name="destination_full_san" id="destination_full_san" required>

      <button type="submit" name="action" value="full">Generate Full Command</button>
    </form>

    {% if full_command %}
    <h2>Generated Full Command:</h2>
    <pre id="zfsCommand">{{ full_command }}</pre>
    <button class="copy-button" onclick="copyToClipboard()">Copy Full Command</button>
    {% endif %}
  </body>
</html>
'''

# Route to handle ZFS command generation via HTTP GET and POST methods
@app.route('/', methods=['GET', 'POST'])
def zfs_command_generator():
    # Initialize the command variables to None; these will hold the final ZFS commands
    incremental_command = None
    full_command = None

    # Check if the request method is POST (i.e., form submitted)
    if request.method == 'POST':
        # Get the action type (incremental or full) from the form
        action = request.form['action']

        # Handle the generation of an incremental ZFS send command
        if action == 'incremental':
            # Retrieve form data for incremental send
            first_snapshot = request.form['first_snapshot']  # First snapshot in the incremental range
            last_snapshot = request.form['last_snapshot']    # Last snapshot in the incremental range
            destination_san = request.form['destination_san']  # Destination SAN server
            force_sync = 'force_sync' in request.form  # Check if the force sync checkbox is checked

            # Extract the zpool name from the first snapshot (assumed to be the first part of the path)
            first_snapshot_prefix = first_snapshot.split('/')[0]  # Extract the zpool name (e.g., hqs1p1)

            # Choose the appropriate ZFS send flag based on whether force sync is enabled
            flag = "-sF" if force_sync else "-s"

            # Append 'p1' to the destination SAN to construct the destination pool name
            destination_pool = f"{destination_san}p1"

            # Check if the destination SAN matches the first two characters of the zpool prefix, then append '-san'
            if destination_san.startswith(first_snapshot_prefix[:2]):
                destination_san += "-san"

            # Extract the dataset name from the snapshot (everything after the first '/')
            dataset_name = first_snapshot.split('@')[0].split('/', 1)[1]

            # Construct the incremental ZFS send command with mbuffer for optimized data transfer
            incremental_command = (
                f'zfs send -c -RI {first_snapshot} {last_snapshot} | '
                f'mbuffer -s 4M -m 8G | ssh {destination_san} '
                f'"mbuffer -s 4M -m 8G | zfs receive {flag} {destination_pool}/{dataset_name}"'
            )

        # Handle the generation of a full ZFS send command
        elif action == 'full':
            # Retrieve form data for full send
            full_snapshot = request.form['full_snapshot']  # Full snapshot to send
            destination_full_san = request.form['destination_full_san']  # Destination SAN server for full snapshot

            # Append 'p1' to the destination SAN to construct the destination pool name
            destination_full_pool = f"{destination_full_san}p1"

            # Extract the dataset name from the snapshot (everything after the first '/')
            dataset_name = full_snapshot.split('@')[0].split('/', 1)[1]

            # Extract the zpool name from the full snapshot to check if destination SAN matches
            full_snapshot_prefix = full_snapshot.split('/')[0]  # Get the zpool name
            if destination_full_san.startswith(full_snapshot_prefix[:2]):
                destination_full_san += "-san"

            # Construct the full ZFS send command with mbuffer for optimized data transfer
            full_command = (
                f'zfs send -c {full_snapshot} | '
                f'mbuffer -s 4M -m 4G | ssh {destination_full_san} '
                f'"mbuffer -s 4M -m 4G | zfs receive -F {destination_full_pool}/{dataset_name}"'
            )

    # Render the form and pass the generated ZFS commands back to the template
    return render_template_string(form_template, incremental_command=incremental_command, full_command=full_command)

# Entry point for running the Flask application in debug mode
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

