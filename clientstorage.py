import sqlalchemy
import datetime
from sqlalchemy.orm import mapper, sessionmaker
from common.variables import *


class ClientDatabase:
    
    class Contacts:
        def __init__(self, contact):
            self.id = None
            self.username = contact
            
    class MessageHistory:
        def __init__(self, to_user, from_user, message):
            self.id = None
            self.to_user = to_user
            self.from_user = from_user
            self.message = message
            self.date = datetime.datetime.now()
            
    
    def __init__(self, name):
        self.database_engine = sqlalchemy.create_engine(f'sqlite:///client_{name}.db3', echo=False,
                                                        connect_args={'check_same_thread': False})
        self.metadata = sqlalchemy.MetaData()
        
        contacts_table = sqlalchemy.Table('contacts', self.metadata,
                                          sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
                                          sqlalchemy.Column('username', sqlalchemy.String)
                                          )
        
        message_history_table = sqlalchemy.Table('message_history', self.metadata,
                                                 sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
                                                 sqlalchemy.Column('to_user', sqlalchemy.String),
                                                 sqlalchemy.Column('from_user', sqlalchemy.String),
                                                 sqlalchemy.Column('message', sqlalchemy.Text),
                                                 sqlalchemy.Column('date', sqlalchemy.DateTime)
                                                 )
        
        self.metadata.create_all(self.database_engine)
        
        mapper(self.Contacts, contacts_table)
        mapper(self.MessageHistory, message_history_table)
        
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()
        
        
    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(username=contact).count():
            new_contact = self.Contacts(contact)
            self.session.add(new_contact)
            self.session.commit()
    
    def del_contact(self, contact):
        self.session.query(self.Contacts).filter_by(username=contact).delete()
        self.session.commit()
        
    def save_message_history(self, to_user, from_user, message):
        message = self.MessageHistory(to_user, from_user, message)
        self.session.add(message)
        self.session.commit()