import smtplib

EMAIL_ADDRESS = "mfadly090@mhs.mdp.ac.id"  
EMAIL_PASSWORD = "vhzd wazu dhmy sfoj" 

try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()  # Menggunakan TLS
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    print("Login berhasil!")
    server.quit()
except smtplib.SMTPAuthenticationError as e:
    print(f"SMTP Authentication Error: {e}")
