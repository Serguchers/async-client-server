from enum import unique
import sqlite3
import sqlalchemy
import datetime
from sqlalchemy.orm import mapper, sessionmaker
from common.variables import SERVER_DATABASE


class ServerStorage:
    class Users:
        def __init__(self, username):
            self.id = None
            self.name = username
            self.last_login = datetime.datetime.now()
    
    class ActiveUsers:
        def __init__(self, user_id, ip_address, port, login_time):
            self.id = None
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            
    class LoginHistory:
        def __init__(self, user_id, login_date, ip_address, port):
            self.id = None
            self.user = user_id
            self.login_date = login_date
            self.ip_address = ip_address
            self.port = port
            
    class UsersContacts:
        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact
            
    class UsersStatistics:
        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0
    
    def __init__(self):
        self.database_engine = sqlalchemy.create_engine(SERVER_DATABASE, echo=False)
        self.metadata = sqlalchemy.MetaData()
        
        users_table = sqlalchemy.Table('Users', self.metadata,
                                       sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
                                       sqlalchemy.Column('name', sqlalchemy.String, unique=True),
                                       sqlalchemy.Column('last_login', sqlalchemy.DateTime))
        
        active_users_table = sqlalchemy.Table('Active_users', self.metadata,
                                       sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
                                       sqlalchemy.Column('user', sqlalchemy.ForeignKey('Users.id'), unique=True),
                                       sqlalchemy.Column('ip_address', sqlalchemy.String),
                                       sqlalchemy.Column('port', sqlalchemy.Integer),
                                       sqlalchemy.Column('login_time', sqlalchemy.DateTime))
        
        login_history_table = sqlalchemy.Table('Login_history', self.metadata,
                                       sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
                                       sqlalchemy.Column('user', sqlalchemy.ForeignKey('Users.id')),
                                       sqlalchemy.Column('login_time', sqlalchemy.DateTime),
                                       sqlalchemy.Column('ip_address', sqlalchemy.String),
                                       sqlalchemy.Column('port', sqlalchemy.Integer))
        
        user_contacts_table = sqlalchemy.Table('User_contacts', self.metadata,
                                        sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
                                        sqlalchemy.Column('user', sqlalchemy.ForeignKey('Users.id')),
                                        sqlalchemy.Column('contact', sqlalchemy.ForeignKey('Users.id')))
        
        user_statistics_table = sqlalchemy.Table('User_statistics', self.metadata,
                                        sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
                                        sqlalchemy.Column('user', sqlalchemy.ForeignKey('Users.id'), unique=True),
                                        sqlalchemy.Column('sent', sqlalchemy.Integer),
                                        sqlalchemy.Column('accepted', sqlalchemy.Integer))
        
        self.metadata.create_all(self.database_engine)
        mapper(self.Users, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, login_history_table)
        mapper(self.UsersContacts, user_contacts_table)
        mapper(self.UsersStatistics, user_statistics_table)
        
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()
        
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()
        
    def login_user(self, username, ip_address, port):
        user_check = self.session.query(self.Users).filter_by(name=username)
        if user_check.count():
            user = user_check.first()
            user.last_login = datetime.datetime.now()
        else:
            user = self.Users(username)
            self.session.add(user)
            self.session.commit()
            user_statistics = self.UsersStatistics(user.id)
            self.session.add(user_statistics)
            self.session.commit()
        
        new_active_user = self.ActiveUsers(user.id, ip_address, port, datetime.datetime.now())
        self.session.add(new_active_user)
        
        history = self.LoginHistory(user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(history)
        
        self.session.commit()
    
    def logout_user(self, username):
        user = self.session.query(self.Users).filter_by(name=username).first()
        self.session.query(self.ActiveUsers).flter_by(user=user.id).delete()
        
        self.session.commit()
        
    def add_contact(self, username, contact):
        user = self.session.query(self.Users).filter_by(name=username).first()
        contact = self.session.query(self.Users).filter_by(name=contact).first()
        contact_check = self.session.query(self.UsersContacts).filter_by(user=user.id, contact=contact.id)
        if contact_check.count():
            return
        user_contact = self.UsersContacts(user.id, contact.id)
        self.session.add(user_contact)
        self.session.commit()
        
    def del_contact(self, username, contact):
        user = self.session.query(self.Users).filter_by(name=username).first()
        contact = self.session.query(self.Users).filter_by(name=contact).first()
        contact_check = self.session.query(self.UsersContacts).filter_by(user=user.id, contact=contact.id)
        if contact_check.count():
            contact_check.delete()
            self.session.commit()
        return
    
    def write_statistics(self, username, action):
        user = self.session.query(self.Users).filter_by(name=username).first()
        user_stats = self.session.query(self.UsersStatistics).filter_by(user=user.id).first()
        if action == 'accepted':
            user_stats.accepted += 1
        if action == 'sent':
            user_stats.sent += 1
        self.session.commit()