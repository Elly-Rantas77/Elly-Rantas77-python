import ipaddress
import subprocess
import platform
import socket
import concurrent.futures
from scapy.all import ARP, Ether, srp
import requests

# Favorites list stored in memory
favorites = ["192.168.8.1/24"]

# ARP scan function
def arp_scan(network_range):
    print(f"\n🔍 Starting ARP scan on {network_range}...\n")
    try:
        arp = ARP(pdst=network_range)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether / arp

        result = srp(packet, timeout=2, verbose=0)[0]

        devices = []
        for sent, received in result:
            devices.append({'ip': received.psrc, 'mac': received.hwsrc})

        if devices:
            print("📋 Devices found:")
            print("IP" + " " * 18 + "MAC")
            print("-" * 40)
            for device in devices:
                print(f"{device['ip']:20} {device['mac']}")
        else:
            print("⚠️ No devices found.")
    except Exception as e:
        print(f"❌ Error during ARP scan: {e}")

# Ping a single host
def ping_host(ip):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    try:
        timeout_param = "-w" if platform.system().lower() == "windows" else "-W"
        timeout_value = "1000" if platform.system().lower() == "windows" else "1"

        result = subprocess.run(
            ["ping", param, "1", timeout_param, timeout_value, str(ip)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if result.returncode == 0:
            print(f"✅ Host is up: {ip}")
            return str(ip)
    except Exception as e:
        print(f"❌ Ping error for {ip}: {e}")
    return None

# Multi-threaded ping scan
def ping_scan(network_range):
    print(f"\n📡 Multi-threaded ping scan on {network_range}...\n")

    try:
        net = ipaddress.IPv4Network(network_range, strict=False)
    except ValueError as e:
        print(f"❌ Invalid network range: {e}")
        return

    alive_hosts = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = {executor.submit(ping_host, ip): ip for ip in net.hosts()}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                alive_hosts.append(result)

    print(f"\n🎉 Scan complete. {len(alive_hosts)} host(s) are up.")

    if alive_hosts:
        do_ports = input("🔍 Do you want to port scan the found hosts? (y/n): ").strip().lower()
        if do_ports == "y":
            for host in alive_hosts:
                port_scan(host)

# Port scanning function
def port_scan(ip, ports=None):
    if ports is None:
        ports = [22, 23, 53, 80, 443, 3389, 8080]

    print(f"\n🔌 Scanning ports on {ip}...")

    open_ports = []

    for port in ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.5)
                result = sock.connect_ex((ip, port))
                if result == 0:
                    open_ports.append(port)
        except Exception:
            pass

    if open_ports:
        print(f"🟢 Open ports on {ip}: {', '.join(map(str, open_ports))}")
    else:
        print(f"🔒 No open common ports found on {ip}.")

# Traceroute function
def traceroute():
    target = input("Enter target IP or hostname for traceroute: ").strip()
    if not target:
        print("⚠️ Target cannot be empty.")
        return

    print(f"\n🛣️ Traceroute to {target}:\n")

    system = platform.system().lower()
    if system == "windows":
        cmd = ["tracert", target]
    else:
        cmd = ["traceroute", target]

    try:
        subprocess.run(cmd)
    except Exception as e:
        print(f"❌ Traceroute failed: {e}")

# DNS Lookup function
def dns_lookup():
    hostname = input("Enter hostname to resolve to IP: ").strip()
    if not hostname:
        print("⚠️ Hostname cannot be empty.")
        return

    try:
        result = socket.gethostbyname_ex(hostname)
        print(f"\n🌐 DNS Lookup Results for {hostname}:")
        print(f"Official name: {result[0]}")
        print(f"Aliases: {result[1]}")
        print(f"IP addresses: {result[2]}")
    except Exception as e:
        print(f"❌ DNS lookup failed: {e}")

# Helper function to validate IP address
def is_valid_ip(ip):
    try:
        ipaddress.IPv4Address(ip)
        return True
    except ipaddress.AddressValueError:
        return False

# Reverse DNS Lookup function
def reverse_dns_lookup():
    ip = input("Enter IP address for reverse DNS lookup: ").strip()
    if not is_valid_ip(ip):
        print("❌ Invalid IP address format.")
        return
    try:
        result = socket.gethostbyaddr(ip)
        print(f"\n🌐 Reverse DNS Lookup for {ip}:")
        print(f"Hostname: {result[0]}")
        print(f"Aliases: {result[1]}")
        print(f"IP addresses: {result[2]}")
    except Exception as e:
        print(f"❌ Reverse DNS lookup failed: {e}")

# Subnet Calculator function
def subnet_calculator():
    ip_input = input("Enter IP address (e.g., 192.168.1.10): ").strip()
    mask_input = input("Enter subnet mask or prefix length (e.g., 255.255.255.0 or 24): ").strip()

    if not ip_input or not mask_input:
        print("⚠️ Both IP and mask/prefix are required.")
        return

    try:
        # If mask_input is a number (prefix length), convert to int
        if mask_input.isdigit():
            prefix = int(mask_input)
            network = ipaddress.IPv4Network(f"{ip_input}/{prefix}", strict=False)
        else:
            # Else try parse mask as netmask and convert to prefix length
            net = ipaddress.IPv4Network(f"{ip_input}/{mask_input}", strict=False)
            network = net

        print(f"\n📊 Subnet details for {ip_input} with mask {mask_input}:")
        print(f"Network address: {network.network_address}")
        print(f"Broadcast address: {network.broadcast_address}")
        print(f"Subnet mask: {network.netmask}")
        print(f"Prefix length: /{network.prefixlen}")
        print(f"Number of usable hosts: {network.num_addresses - 2 if network.num_addresses > 2 else network.num_addresses}")
        print(f"Usable IP range: {network.network_address + 1} - {network.broadcast_address - 1}")
    except Exception as e:
        print(f"❌ Invalid input or error calculating subnet: {e}")

# MAC Vendor Lookup function
def mac_vendor_lookup():
    mac = input("Enter MAC address (e.g., 44:38:39:ff:ef:57): ").strip()
    if not mac:
        print("⚠️ MAC address cannot be empty.")
        return

    # Normalize MAC address for API (remove separators)
    normalized_mac = mac.replace(":", "").replace("-", "").lower()

    # Use https://api.macvendors.com API
    url = f"https://api.macvendors.com/{normalized_mac}"

    print(f"\n🔍 Looking up vendor info for MAC: {mac} ...")
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            vendor = response.text
            print(f"🏭 Vendor: {vendor}")
        else:
            print(f"⚠️ Vendor info not found or API error (status code {response.status_code}).")
    except Exception as e:
        print(f"❌ Error during MAC vendor lookup: {e}")

# Helper to get validated menu choice
def get_menu_choice(num_options):
    while True:
        choice = input(f"🔸 Select an option (1-{num_options}): ").strip()
        if choice.isdigit():
            choice_int = int(choice)
            if 1 <= choice_int <= num_options:
                return choice_int
        print("❌ Invalid input. Please enter a number within the menu options.")

# Main menu
def menu():
    default_network = "192.168.8.1/24"
    while True:
        print("\n==============================")
        print("📡 NETWORK SCANNER MAIN MENU")
        print("==============================")
        print("1. ARP Scan: Default network (192.168.8.1/24)")
        print("2. ARP Scan: Enter custom network range")
        print("3. ARP Scan: Scan from favorites")
        print("4. ARP Scan: Custom wide IP range")
        print("5. Manage favorites: Add a new range")
        print("6. ICMP Scan: Ping scan custom IP range")
        print("7. Traceroute")
        print("8. DNS Lookup (hostname -> IP)")
        print("9. Reverse DNS Lookup (IP -> hostname)")
        print("10. Subnet Calculator")
        print("11. MAC Vendor Lookup")
        print("12. Exit")
        print("==============================")

        choice = get_menu_choice(12)

        if choice == 1:
            arp_scan(default_network)

        elif choice == 2:
            custom_network = input("Enter network range (e.g., 192.168.1.0/24): ").strip()
            arp_scan(custom_network)

        elif choice == 3:
            if not favorites:
                print("⚠️ No favorites saved.")
                continue

            print("\n⭐ Favorites:")
            for idx, fav in enumerate(favorites, 1):
                print(f"{idx}. {fav}")
            try:
                fav_choice = int(input("Select a favorite to scan: "))
                if 1 <= fav_choice <= len(favorites):
                    arp_scan(favorites[fav_choice - 1])
                else:
                    print("⚠️ Invalid selection.")
            except ValueError:
                print("⚠️ Please enter a number.")

        elif choice == 4:
            print("\n⚠️ WARNING: This will scan a wide IP range.")
            print("Examples you can try:")
            print(" - 10.0.0.0/8")
            print(" - 172.16.0.0/12")
            print(" - 192.168.0.0/16")
            wide_range = input("Enter wide IP range to scan (ARP will only work locally): ").strip()
            confirm = input(f"Proceed with ARP scan on {wide_range}? (y/n): ").strip().lower()
            if confirm == "y":
                arp_scan(wide_range)
            else:
                print("❌ Scan canceled.")

        elif choice == 5:
            new_fav = input("Enter a network range to add to favorites (e.g., 192.168.1.0/24): ").strip()
            if not new_fav:
                print("⚠️ You must enter a valid network.")
            elif new_fav in favorites:
                print("ℹ️ That range is already in favorites.")
            else:
                favorites.append(new_fav)
                print(f"✅ Added '{new_fav}' to favorites.")

        elif choice == 6:
            custom_range = input("Enter IP range to ping scan (e.g., 8.8.8.0/24): ").strip()
            confirm = input(f"⚠️ This will ping all hosts in {custom_range}. Proceed? (y/n): ").strip().lower()
            if confirm == "y":
                ping_scan(custom_range)
            else:
                print("❌ Scan canceled.")

        elif choice == 7:
            traceroute()

        elif choice == 8:
            dns_lookup()

        elif choice == 9:
            reverse_dns_lookup()

        elif choice == 10:
            subnet_calculator()

        elif choice == 11:
            mac_vendor_lookup()

        elif choice == 12:
            print("👋 Exiting program. Goodbye!")
            break

if __name__ == "__main__":
    menu()
