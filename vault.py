#!/usr/bin/env python3.6

# Author: Sarthak Patidar <sarthakpatidar15@gmail.com>
from cmd import Cmd
from pymongo import MongoClient, DeleteOne, InsertOne, ReplaceOne
from pymongo.errors import ServerSelectionTimeoutError
import sys, getpass


class MyPrompt(Cmd):
    def encrypt(self, raw):
        encrypted = ''

        for i in range(0, len(raw)):
            encrypted = encrypted + chr(ord(raw[i]) - 2)

        return encrypted

    def decrypt(self, encrypted):
        raw = ''

        for i in range(0, len(encrypted)):
            raw = raw + chr(ord(encrypted[i]) + 2)

        return raw

    def get_id(self):
        results = credentials.find()
        id = 0
        for result in results:
            id = int(result['credential_id'])

        return id + 1

    def print_multiple(self, results, command):
        for result in results:
            print ('Enter ' + str(result['credential_id']) + ' to '+command+': ' + result['username'] + ' (' + result['comments'] + ')')

    def view_single(self, result):
        pwd = result['password']
        raw = self.decrypt(pwd)
        print('Username :' + result['username'])
        print('Password :' + raw+'\n')

    def view_multiple(self, results):
        for result in results:
            self.view_single(result)

    def update_single(self, old,to_update):
        new_username = ''
        new_password = ''
        new_comment = ''
        for type in to_update:
            if type == 'username':
                new_username += getpass.getpass('Enter new username for ' + old['vendor'] + ': ')
            elif type == 'password':
                new_password += getpass.getpass('Enter new password for ' + old['vendor'] + ': ')
            elif type == 'comments':
                new_comment += input('Enter new comments for ' + old['vendor'] + ': ')
            else:
                print('You can not update ' + type + ' for ' + old['vendor'] + '.')

        if not len(new_username):
            new_username += old['username']

        if not len(new_password):
            new_password += old['password']
        else:
            new_password = self.encrypt(new_password)

        if not len(new_comment):
            new_comment += old['comments']

        new_credential = {
            'vendor': old['vendor'],
            'credential_id': old['credential_id'],
            'username': new_username,
            'password': new_password,
            'comments': new_comment,
            'user': old['user']
        }

        credentials.update(old, new_credential)

        print('Updated Successfully')

    def cmdloop(self,intro='Vault Version 2.0.8 developed by Sarthak Patidar'):
        try:
            while True:
                try:
                    super(MyPrompt, self).cmdloop(intro="Vault Version 2.0.8 developed by Sarthak Patidar")
                    break
                except KeyboardInterrupt:
                    print('\n')
                    self.do_quit(intro)
        except ServerSelectionTimeoutError:
            print('Cannot Connect to Vault Database. Please start MongoDB Server.')

    def check_username(self, old_name):
        if len(old_name):
            results = users.find({'username': old_name})
            count = results.count()

            if count == 0:
                return old_name

            if count >= 1:
                print('Username \''+old_name+'\' already exists. Please enter a different username.'+'\n')
                new_name = input('Enter username of new user: ')
                return self.check_username(new_name)

        else:
            print('Username cannot be empty.')
            uname = input('Enter username of new user: ')
            while not len(uname):
                uname = input('Enter username of new user: ')

            self.check_username(uname)

    def check_superuser(self):
        results = users.find({'username': sys.argv[2]})
        if results.count() == 1:
            for user in results:
                if user['superuser']:
                    return True
                else:
                    print('You do not have superuser privileges to access this area.')
                    return False

    def do_save(self, args):
        """Saves credentials."""
        try:
            argv = args.split(' ')
            vendor = argv[0]

            while not len(vendor):
                vendor += input('Enter Vendor Name: ')
            comments = ''

            if len(argv) > 1:
                del argv[0]

                comments += ' '.join(argv)

            uname = getpass.getpass('Enter username for '+vendor+': ')
            while not len(uname):
                print('Username cannot be empty')
                uname = getpass.getpass('Enter username for ' + vendor + ': ')

            pwd = getpass.getpass('Enter password for ' + vendor + ': ')
            while not len(pwd):
                print('Password cannot be empty')
                pwd = getpass.getpass('Enter password for ' + vendor + ': ')

            encrypted_pwd = self.encrypt(pwd)
            credential = {
                'vendor': vendor,
                'credential_id': self.get_id(),
                'username': uname,
                'password': encrypted_pwd,
                'comments': comments,
                'user': sys.argv[2]
            }

            result = credentials.insert_one(credential)
            if result:
                print('Saved Successfully')
            else:
                print('Unable to save credentials')

        except IndexError:
            print('Insufficient number of arguments.')

    def do_see(self, args):
        """Shows saved credentials."""
        if not len(args):
            vendor = input('Enter name of vendor: ')
            while not len(vendor):
                vendor = input('Enter name of vendor: ')

        else:
            vendor = args

        results = credentials.find({'vendor': vendor, 'user': sys.argv[2]})
        if results is not None:
            number = results.count()
            print(str(number) + ' Account/s found for ' + vendor)
            if number > 1:
                self.print_multiple(results, 'view')

                print('Or enter 0 to see all passwords.')
                see = int(input('> '))
                if see == 0:
                    see_all_results = credentials.find({'vendor': vendor, 'user': sys.argv[2]})
                    self.view_multiple(see_all_results)

                else:
                    result = credentials.find_one({'vendor': vendor, 'credential_id': see, 'user': sys.argv[2]})
                    if result is not None:
                        self.view_single(result)

                    else:
                        print('Incorrect Key.')

            else:
                self.view_multiple(results)

        else:
            print ('No credentials exist for '+vendor+'.')

    def do_update(self, args):
        """Updates a particular credentials."""
        to_update = args.split(' -')
        vendor = to_update[0]
        del to_update[0]

        results = credentials.find({'vendor': vendor, 'user': sys.argv[2]})
        if results is not None:
            number = results.count()
            print(str(number) + ' Account/s found for ' + vendor)
            if number > 1:
                self.print_multiple(results, 'update')
                update = int(input('> '))

                result = credentials.find_one({'vendor': vendor, 'credential_id': update, 'user': sys.argv[2]})
                if result is not None:
                    self.update_single(result, to_update)
                else:
                    print('Incorrect Key.')

            else:
                self.update_single(results, to_update)

    def do_delete(self, args):
        """Deletes a particular credentials."""
        vendor = args
        pwd = getpass.getpass('Enter Password for '+username+': ')
        if pwd == 'Srth#hak2411':
            results = credentials.find({'vendor': args})
            if results is not None:
                number = results.count()
                print(str(number) + ' Account/s found for ' + vendor)
                if number > 1:
                    self.print_multiple(results, 'delete')
                    delete = int(input('> '))

                    result = credentials.find_one({'vendor': vendor, 'credential_id': delete, 'user': sys.argv[2]})
                    if result is not None:
                        credentials.remove(result)

                    else:
                        print('Incorrect Key.')

                else:
                    credentials.remove(results)

            else:
                print('No credentials found for '+args+'.')

        else:
            print('Access Denied. Invalid Password')

    def do_quit(self, args):
        """Quits the program."""
        print ('Logged out. Bye.')
        raise SystemExit

    def do_create(self, args):
        """Creates a new user.
        only for superusers"""
        if self.check_superuser():
            create_username = input('Enter username of new user: ')
            uname = self.check_username(create_username)

            if uname is not None:
                create_pwd = getpass.getpass('Enter password for '+str(uname)+': ')
                create_password = self.encrypt(create_pwd)

                if args == '-superuser':
                    user = {
                    'username': uname,
                    'password': create_password,
                    'superuser': True
                    }

                else:
                    user = {
                        'username': uname,
                        'password': create_password,
                        'superuser': False
                    }

                db.users.insert(user)

                print('New User \''+uname+'\' Created.')

    def do_users(self, args):
        """See All Registered Users only for superusers"""
        if self.check_superuser():
            all_users = users.find({})
            for user in all_users:
                print (str(user)+'\n')


def pass_encrypt(raw):
    encrypted = ''

    for i in range(0, len(raw)):
        encrypted = encrypted + chr(ord(raw[i]) - 2)

    return encrypted


def check_user(username):
    user = users.find({
            'username': username
            # 'password': password
           })
    for u in user:
        print(u)


if __name__ == '__main__':
    try:
        if sys.argv[1] == '-u' and sys.argv[3] == '-p':
            try:
                client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=1)
                db = client.vault  # selecting vault database as default db
                credentials = db.credentials
                users = db.users
                check_user(sys.argv[2])
                #
                # user = users.find({'username': username})
                # length = user.count()
                # if length:
                #     password = getpass.getpass('Enter Password for '+username+': ')
                #     pwd = pass_encrypt(password)
                #     user1 = users.find({'username': username, 'password': pwd})
                #     length1 = user1.count()
                #
                #     if length1:
                #         print('Welcome '+username+'!')
                #         prompt = MyPrompt()
                #         prompt.prompt = ': '
                #         print('Initializing Vault...')
                #         prompt.cmdloop('Vault Version 2.0.8 developed by Sarthak Patidar')
                #
                #     else:
                #         print('Access Denied for '+username+'. Invalid Password.')
                #
                # else:
                #     print('User \''+username+'\' does not exist.')
                #
            except ServerSelectionTimeoutError:
                print('Cannot Connect to Vault Database. Please start MongoDB Server.')

        else:
            print('Invalid Arguments.')

    except IndexError:
        print('Access Denied.')
