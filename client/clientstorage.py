import os
import sys

sys.path.append(os.getcwd())
sys.path.append(os.path.dirname(__file__))

import sqlalchemy
import datetime
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy import or_
from common.variables import *


class ClientDatabase:
    class Contacts:
        def __init__(self, contact):
            self.id = None
            self.username = contact

    class KnownUsers:
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
        self.database_engine = sqlalchemy.create_engine(
            f"sqlite:///{os.path.dirname(__file__)}/databases/client_{name}.db3",
            echo=False,
            pool_recycle=7200,
            connect_args={"check_same_thread": False},
        )
        self.metadata = sqlalchemy.MetaData()

        contacts_table = sqlalchemy.Table(
            "contacts",
            self.metadata,
            sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column("username", sqlalchemy.String),
        )

        known_users_table = sqlalchemy.Table(
            "known_users",
            self.metadata,
            sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column("username", sqlalchemy.String),
        )

        message_history_table = sqlalchemy.Table(
            "message_history",
            self.metadata,
            sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column("to_user", sqlalchemy.String),
            sqlalchemy.Column("from_user", sqlalchemy.String),
            sqlalchemy.Column("message", sqlalchemy.Text),
            sqlalchemy.Column("date", sqlalchemy.DateTime),
        )

        self.metadata.create_all(self.database_engine)

        mapper(self.Contacts, contacts_table)
        mapper(self.MessageHistory, message_history_table)
        mapper(self.KnownUsers, known_users_table)

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

    def get_message_history(self, contact):
        message_history = (
            self.session.query(
                self.MessageHistory.to_user,
                self.MessageHistory.from_user,
                self.MessageHistory.date,
                self.MessageHistory.message,
            )
            .filter(
                or_(
                    self.MessageHistory.to_user == contact,
                    self.MessageHistory.from_user == contact,
                )
            )
            .all()
        )
        self.session.commit()
        return message_history

    def get_contacts(self):
        return [
            contact[0] for contact in self.session.query(self.Contacts.username).all()
        ]

    def meet_user(self, contact):
        if not self.session.query(self.KnownUsers).filter_by(username=contact).count():
            met_user = self.KnownUsers(contact)
            self.session.add(met_user)
            self.session.commit()

    def get_known_users(self):
        return [user[0] for user in self.session.query(self.KnownUsers.username).all()]


if __name__ == "__main__":
    pass
