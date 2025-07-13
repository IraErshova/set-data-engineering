from cassandra.cluster import Cluster

class CassandraCreateSchemas:
    def __init__(self, host: str = 'localhost', port: int = 9042, keyspace: str = 'my_keyspace'):
        self.host = host
        self.port = port
        self.keyspace = keyspace
        self.cluster = None
        self.session = None
        self._connect()

    def _connect(self):
        try:
            self.cluster = Cluster([self.host], port=self.port)
            self.session = self.cluster.connect()
            print("Connected to Cassandra cluster")
        except Exception as e:
            print(f"Error connecting to Cassandra: {e}")
            raise

    def create_keyspace(self):
        try:
            if self.session is None:
                raise Exception("Session is not initialized.")
            self.session.execute(f"""
                CREATE KEYSPACE IF NOT EXISTS {self.keyspace}
                WITH replication = {{
                    'class': 'SimpleStrategy',
                    'replication_factor': 1
                }}
            """)
            self.session.set_keyspace(self.keyspace)
            print(f"Connected to {self.keyspace}")
        except Exception as e:
            print(f"Error creating keyspace: {e}")
            raise

    def execute_cql_file(self, file_path):
        with open(file_path, 'r') as f:
            cql_commands = f.read()

        statements = cql_commands.split(';')

        for command in statements:
            command = command.strip()
            if command:  # avoid executing empty strings
                try:
                    self.session.execute(command)
                    print(f"Executed: {command[:60]}...")
                except Exception as e:
                    print(f"Failed to execute command:\n{command}\nError: {e}")

    def close(self):
        if self.session:
            self.session.shutdown()
        if self.cluster:
            self.cluster.shutdown()

if __name__ == "__main__":
    manager = None
    try:
        manager = CassandraCreateSchemas()
        manager.create_keyspace()
        manager.execute_cql_file("cql_scripts/create_schemas.cql")
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        if manager:
            manager.close()