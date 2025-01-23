import streamlit as st

# Title of the app
st.title("ZFS Command Generator")

# Sidebar for navigation
st.sidebar.title("ZFS Command Options")
action = st.sidebar.radio("Select Action", ["Incremental Command", "Full Command"])

# Helper function to copy command to clipboard
def copy_to_clipboard(command):
    try:
        import pyperclip
        pyperclip.copy(command)
        st.success("Command copied to clipboard!")
    except Exception as e:
        st.error(f"Failed to copy: {e}")

if action == "Incremental Command":
    st.header("Generate Incremental ZFS Command")
 
    # Form inputs for incremental command
    first_snapshot = st.text_input("First Incremental Snapshot")
    last_snapshot = st.text_input("Last Incremental Snapshot")
    destination_san = st.text_input("Destination SAN for Incrementals")
    force_sync = st.checkbox("Force Sync (-F): (Will Mirror Source)")
    compression = st.checkbox("Enable Compression (-c)", value=True)

    if st.button("Generate and Copy Incremental Command"):
        if first_snapshot and last_snapshot and destination_san:
            first_snapshot_prefix = first_snapshot.split('/')[0]
            compression_flag = "-c" if compression else ""
            flag = "-sF" if force_sync else "-s"
            destination_pool = f"{destination_san}p1"

            if destination_san.startswith(first_snapshot_prefix[:2]):
                destination_san += "-san"

            dataset_name = first_snapshot.split('@')[0].split('/', 1)[1]
            incremental_command = (
                f'zfs send {compression_flag} -RI {first_snapshot} {last_snapshot} | '
                f'mbuffer -s 4M -m 8G | ssh {destination_san} '
                f'"mbuffer -s 4M -m 8G | zfs receive {flag} {destination_pool}/{dataset_name}"'
            )

            st.code(incremental_command, language="bash")
            copy_to_clipboard(incremental_command)
        else:
            st.warning("Please fill in all fields.")

elif action == "Full Command":
    st.header("Generate Full ZFS Command")

    # Form inputs for full command
    full_snapshot = st.text_input("Full Snapshot")
    destination_full_san = st.text_input("Destination SAN for Full Snapshot")

    if st.button("Generate and Copy Full Command"):
        if full_snapshot and destination_full_san:
            destination_full_pool = f"{destination_full_san}p1"
            full_snapshot_prefix = full_snapshot.split('/')[0]

            if destination_full_san.startswith(full_snapshot_prefix[:2]):
                destination_full_san += "-san"

            dataset_name = full_snapshot.split('@')[0].split('/', 1)[1]
            full_command = (
                f'zfs send -c {full_snapshot} | '
                f'mbuffer -s 4M -m 4G | ssh {destination_full_san} '
                f'"mbuffer -s 4M -m 4G | zfs receive -F {destination_full_pool}/{dataset_name}"'
            )

            st.code(full_command, language="bash")
            copy_to_clipboard(full_command)
        else:
            st.warning("Please fill in all fields.")
