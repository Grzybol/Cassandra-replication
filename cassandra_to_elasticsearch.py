from cassandra.cluster import Cluster, DCAwareRoundRobinPolicy
from cassandra.query import SimpleStatement
from elasticsearch import Elasticsearch, helpers
from datetime import datetime
import time
import logging

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfiguracja połączenia z Cassandrą
cassandra_host = '127.0.0.1'  # Host lokalny
cassandra_port = 9042         # Port CQL dla cass1
keyspace = 'logging'

# Ustawienie protocol_version i load_balancing_policy
cluster = Cluster(
    contact_points=[cassandra_host],
    port=cassandra_port,
    protocol_version=5,  # Zamień na odpowiednią wersję dla Twojej Cassandry
    load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='dc1')
)
session = cluster.connect(keyspace)

# Konfiguracja połączenia z Elasticsearch z uwierzytelnianiem
es_host = ''
es_port = 
es_user = ''     
es_password = '' 
es_api_key = ''

# Użycie API Key, kompatybilne z wersją 8.x
es = Elasticsearch(
    [f"http://{es_host}:{es_port}"],
    api_key=es_api_key,
    verify_certs=False           # Ustaw na True, jeśli używasz SSL
)

# Użycie pełnego URL, kompatybilne z wersją 8.x
#es = Elasticsearch(
 #   [f"http://{es_host}:{es_port}"],
  #  basic_auth=(es_user, es_password),
   # verify_certs=False           # Ustaw na True, jeśli używasz SSL
#)

def fetch_new_logs(last_timestamp):
    query = """
    SELECT log_id, timestamp, plugin, transactionid, level, message, playername, uuid, servername 
    FROM logs 
    WHERE timestamp > %s ALLOW FILTERING
    """
    statement = SimpleStatement(query, fetch_size=100)
    rows = session.execute(statement, [last_timestamp])
    return rows

def prepare_actions(logs):
    actions = []
    for log in logs:
        action = {
            "_index": "logs",
            "_id": str(log.log_id),
            "_source": {
                "timestamp": log.timestamp.isoformat(),
                "plugin": log.plugin,
                "transactionID": log.transactionid,  # Użyj małych liter
                "level": log.level,
                "message": log.message,
                "playerName": log.playername,         # Użyj małych liter
                "uuid": log.uuid,
                "serverName": log.servername          # Użyj małych liter
            }
        }
        actions.append(action)
    return actions

def main():
    last_timestamp = datetime.min
    while True:
        try:
            new_logs = fetch_new_logs(last_timestamp)
            if new_logs:
                actions = prepare_actions(new_logs)
                helpers.bulk(es, actions)
                # Aktualizacja ostatniego timestampu
                last_timestamp = max(log.timestamp for log in new_logs)
                logger.info(f"Przesłano {len(actions)} logów do Elasticsearch.")
            else:
                logger.info("Brak nowych logów do przesłania.")
        except Exception as e:
            logger.error(f"Błąd podczas przesyłania logów: {e}")
        # Czekaj przed kolejnym sprawdzeniem
        time.sleep(10)  # Sprawdź co 10 sekund

if __name__ == "__main__":
    main()
