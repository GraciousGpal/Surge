# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import asyncio
import logging

import os
import shutil
import sys
import zipfile

import dropbox
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode

logger = logging.getLogger(__name__)
DROPAPI = os.environ['DROPBOXAPI']
dbx = dropbox.Dropbox(DROPAPI)
IGNORED_FILES = ['desktop.ini', 'thumbs.db', '.ds_store', 'icon\r', '.dropbox', '.dropbox.attr']
local_dir = ('data')  # FOR FOLDER UPLOAD


def file_len(fname):
    with open(fname, encoding='utf-8') as f:
        for i, l in enumerate(f):
            pass
    return i + 1


def is_ignored(filename):
    filename_lower = filename.lower()
    for ignored_file in IGNORED_FILES:
        if ignored_file in filename_lower:
            return True
    return False


class dropboxstorage:
    def __init__(self, bot):
        self.bot = bot
        self.modname = "dropboxstorage"
        self.Description = "BacksUp Data to a Dropbox Server"
        self.provision = self.bot.loop.create_task(self.BnU())
        restore("data.zip", "/data.zip")
        unzip()

    async def BnU(self):
        """
        Continuous function that restores and backs up
        :return:
        """
        await self.bot.wait_until_ready()
        while True:
            await asyncio.sleep(60*15)
            await folderzipupload("data")

def restore(file, path):
    # Download the specific revision of the file at BACKUPPATH to LOCALFILE
    try:
        os.remove(file)
        logging.info("[USER.db] Detected Removing.....Done")
    except OSError:
        logging.warning("OSError")
        pass
    try:
        logging.info("Downloading current " + path + " from Dropbox, overwriting " + file + "...")
        dbx.files_download_to_file(file, path)
    except:
        logging.warning("RESTORE FAILED NO DATABASE!!")
        logging.warning("Ignoring and continuing ..")


async def backup(file, path):
    with open(file, 'rb') as f:
        # We use WriteMode=overwrite to make sure that the settings in the file
        # are changed on upload
        logging.info("Uploading " + file + " to Dropbox as " + path + "...")
        try:
            try:
                dbx.files_delete_v2(path)
            except:
                pass
            dbx.files_upload(f.read(), path, mode=dropbox.files.WriteMode.overwrite)
            logging.info("Uploaded!")
        except ApiError as err:
            # This checks for the specific error where a user doesn't have
            # enough Dropbox space quota to upload this file
            if (err.error.is_path() and
                    err.error.get_path().error.is_insufficient_space()):
                sys.exit("ERROR: Cannot back up; insufficient space.")
            elif err.user_message_text:
                logging.warning(err.user_message_text)
                sys.exit()
            else:
                logging.warning(err)
                sys.exit()


async def folderzipupload(file):
    shutil.make_archive("data", 'zip', local_dir)
    path = "/data.zip"
    with open("data.zip", 'rb') as f:
        #  We use WriteMode=overwrite to make sure that the settings in the file
        #  are changed on upload
        logging.info("Uploading " + file + " to Dropbox as " + path + "...")
        try:
            try:
                dbx.files_delete_v2(path)
            except:
                pass
            dbx.files_upload(f.read(), path, mode=dropbox.files.WriteMode.overwrite)
            logging.info("Uploaded!")
        except ApiError as err:
            # This checks for the specific error where a user doesn't have
            # enough Dropbox space quota to upload this file
            if (err.error.is_path() and
                    err.error.get_path().error.is_insufficient_space()):
                sys.exit("ERROR: Cannot back up; insufficient space.")
            elif err.user_message_text:
                logging.warning(err.user_message_text)
                sys.exit()
            else:
                logging.warning(err)
                sys.exit()


def unzip():
    try:
        logging.info("Extracting data.zip ")
        fh = open('data.zip', 'rb')
        z = zipfile.ZipFile(fh)
        for name in z.namelist():
            outpath = "data//"
            z.extract(name, outpath)
        logging.info("Extracted data.zip ")
    except Exception as e :
        logging.error(e)

    try:
        os.remove("data.zip")
    except Exception as e:
        logging.error(e)


def setup(bot):
    bot.add_cog(dropboxstorage(bot))
