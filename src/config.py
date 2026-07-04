import os
from dotenv import load_dotenv
load_dotenv()

producer_conf={
    "bootstrap.servers":os.getenv("BOOTSTRAP_SERVERS"),
    "security.protocol":"SSL",
    "ssl.ca.location":os.getenv("SSL_CA_LOCATION"),
    "ssl.key.location":os.getenv("SSL_KEY_LOCATION"),
    "ssl.certificate.location":os.getenv("SSL_CERT_LOCATION")
}

consumer_conf = {
    "bootstrap.servers": os.getenv("BOOTSTRAP_SERVERS"),
    "group.id": os.getenv("GROUP_ID"),
    "auto.offset.reset": "earliest",
    "security.protocol": "SSL",
    "ssl.ca.location": os.getenv("SSL_CA_LOCATION"),
    "ssl.key.location": os.getenv("SSL_KEY_LOCATION"),
    "ssl.certificate.location": os.getenv("SSL_CERT_LOCATION")
}