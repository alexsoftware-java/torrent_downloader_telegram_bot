import telebot 
from telebot import types
import time
import re
import urllib
import os
import os.path
import subprocess 
import sys
reload(sys)
sys.setdefaultencoding('utf8')


TOKEN = '411001654:AAFG3y_C20jslSqKqUe0Yei0WNW7y55INfM'


#folders to store files, make sure that they're exist
download_folder = '/tbot/files/downloads/'
torrent_files_folder = '/tbot/torrents/'
#/tbot/torrents/documents needed too
download_logs_folder = '/tbot/files/'


knownUsers = []  # todo: save these in a file,
userStep = {}  # so they won't reset every time the bot restarts

commands = {  # command description used in the "help" command
              'start': 'Get used to the bot',
              'help': 'Gives you information about the available commands',
              'downloadTorrent': 'Start downloading'
}

howDownloadTorrentFileSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True)  # create selection keyboard
howDownloadTorrentFileSelect.add('From link', 'From local file', 'From magnet link')

hideBoard = types.ReplyKeyboardRemove()  # if sent as reply_markup, will hide the keyboard


# error handling if user isn't known yet
# (obsolete once known users are saved to file, because all users
#   had to use the /start command and are therefore known to the bot)
def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        knownUsers.append(uid)
	userStep[uid] = 0 
        print "New user detected, who hasn't used \"/start\" yet"
	return 0

# only used for console output
def listener(messages):
    """
    When new messages arrive TeleBot will call this function.
    """
    for m in messages:
        if m.content_type == 'text':
            # print the sent message to the console
            print str(m.chat.first_name) + " [" + str(m.chat.id) + "]: " + m.text


bot = telebot.TeleBot(TOKEN)
bot.set_update_listener(listener)  # register listener


# handle the "/start" command
@bot.message_handler(commands=['start'])
def command_start(m):
    cid = m.chat.id
    if cid not in knownUsers:  # if user hasn't used the "/start" command yet:
        knownUsers.append(cid)  # save user id, so you could brodcast messages to all users of this bot later
        userStep[cid] = 0  # save user id and his current "command level", so he can use the "/getImage" command
        bot.send_message(cid, "Hi and Welcome!",reply_markup=hideBoard)
        bot.send_message(cid, """

	I'm able to download torrents for you and send files via telegram

	Also I can make video smaller to faster download

	""")
        command_help(m)  # show the new user the help page
    else:
        bot.send_message(cid, "Hi, I already know you!",reply_markup=hideBoard)
 	bot.send_message(cid, """

        I'm able to download torrents for you and send files via telegram

        Also I can make video smaller to faster download

        """)
	command_help(m) 


# help page
@bot.message_handler(commands=['help'])
def command_help(m):
    cid = m.chat.id
    help_text = "The following commands are available: \n"
    for key in commands:  # generate help text out of the commands dictionary defined at the top
        help_text += "/" + key + ": "
        help_text += commands[key] + "\n"
    bot.send_message(cid, help_text)  # send the generated help page


# 
@bot.message_handler(commands=['downloadTorrent'])
def command_image(m):
    cid = m.chat.id
    bot.send_message(cid, "Let's start. I'm able to download torrent file from link/meta or you can send it to me directly", reply_markup=howDownloadTorrentFileSelect)  # show the keyboard
    userStep[cid] = 1  # set the user to the next step (expecting a reply in the listener now)

@bot.message_handler(func=lambda message:  get_user_step(message.chat.id) == 0)
def return_to_zero(m):
    cid = m.chat.id
    bot.send_message(cid, "Welcome again. I'm able to download torrent file from link/meta or you can send it to me directly", reply_markup=howDownloadTorrentFileSelect)  # show the keyboard
    userStep[cid] = 1  # set the user to the next step (expecting a reply in the listener now)

# if the user has issued the "/downloadTorrent
@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 1)
def torrent_file_first_select(m):
    cid = m.chat.id
    text = m.text
    # 
    bot.send_chat_action(cid, 'typing')
    if text == "From link":  
	bot.send_message(cid, "Plese send me link to direct torrent file download",reply_markup=hideBoard)
	userStep[cid] = 2 
    elif text == "From local file":
	bot.send_message(cid, "Plese send me torrent file")
    elif text == "From magnet link":
        bot.send_message(cid, "Plese send me torrent Magnet link\n for example: magnet:?xt=urn:btih:49ab498046c32d5eb0e6ea37548fbe8ac736a604 \n link SHOULD start from magnet:")
    elif text == "exit":
	userStep[cid] = 0 

#Download torrent file from link
@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 2)
def torrent_file_from_link(m):
    cid = m.chat.id
    link = m.text
    bot.send_chat_action(cid, 'typing')
    matchLink = re.search('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', link)	
    if (matchLink):
	bot.send_message(cid, "Thanks\nI started to download torrent file from link: " + link)
	file_name = torrent_files_folder + link.split('/')[-1]
        if(re.search('.*\.torrent', file_name)):
  		urllib.urlretrieve (link, file_name)
		time.sleep(1)
		if (os.path.exists(file_name)):	
	    	    time.sleep(1)	
	            bot.send_message(cid, "Ok, downloaded",reply_markup=hideBoard)	
    		else :
		    bot.send_message(cid, "I expect some problems, please try again")	
 		    userStep[cid] = 1	
		f = os.popen('transmission-show ' + file_name)
		torrent_info = f.read()
		bot.send_message(cid, "Torrent info: " + torrent_info)
		filesSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True) 
		filesSelect.add('Yes, please', 'No, stop')
                bot.send_message(cid, "Should I start download?",reply_markup=filesSelect)
	else:
		bot.send_message(cid, "It's not torrent file, please upload torrent file or use link/meta ")
		userStep[cid] = 0
    
    elif( m.text == 'Yes, please' ):
        bot.send_message(cid, "Ok, I start",reply_markup=hideBoard)
	downloader(m, file_name)
    elif (  m.text == 'No, stop') :
        bot.send_message(cid, "Ok, return back")
        userStep[cid] = 0
    elif (not matchLink) :
	bot.send_message(cid, "I didn't recognise your link: " + link)	
	bot.send_message(cid, "Please check format ")

#Recieve torrent file
@bot.message_handler(content_types=['document']) 
def torrent_file_from_user(m):
	cid = m.chat.id
	file_info = bot.get_file(m.document.file_id)
	file_name = m.document.file_name
	if(re.search('.*\.torrent', file_name)):
	    file_location = torrent_files_folder + file_info.file_path
	    link = "https://api.telegram.org/file/bot"+TOKEN+"/"+file_info.file_path
	    urllib.urlretrieve (link, file_location)	
	    bot.send_message(cid, "Ok, file " + file_name + " recived ")	
	    f = os.popen("transmission-show '" + file_location + "' | grep -v '" + torrent_files_folder + "'")
            torrent_info = f.read()
            bot.send_message(cid, "Torrent info: " + torrent_info,reply_markup=hideBoard)
	    downloader(m, file_location)	
	else:
	    bot.send_message(cid, "Wrong file extension. Currently I can work only with .torrent files")


#Magnet link
@bot.message_handler(regexp="^magnet:.*")
def magnet_link(m):
	cid = m.chat.id
	link = m.text
	bot.send_message(cid, "You send me magnet:" + link)
	downloader(m, link)

@bot.message_handler(func=lambda message: message.text == "hi")
def command_text_hi(m):
    bot.send_message(m.chat.id, "hi")

##########TORRENT DOWNLOAD############
#todo add to thread
def downloader(m, link):
	cid = str(m.chat.id)
	bot.send_chat_action(cid, 'typing')
        log_file = download_logs_folder + "down_stats_"+ cid +".txt"

	if not os.path.exists(download_folder + cid):
		os.popen("mkdir" + download_folder + cid)
	
	if (os.path.exists(log_file)):
	     os.popen("rm "+log_file) #DEBUG
		
	if (os.path.exists(download_folder + cid) and os.listdir( download_folder + cid )):
		#already has download files - ask to go to download?
	    bot.send_message(cid, "You have downloaded files in temporary storage")
	    send_files_to_user(m)
	    return #TODO ask yes/no
		
	bot.send_message(cid, "Torrent downloading\nPlease wait few minutes")
       	bot.send_message(cid, "Info about download procces will send every minute")
	
	os.popen("aria2c --conf-path=\'\' '" + link +"' -d " + download_folder + cid +" >> " + log_file + " & ")
	bot.send_chat_action(cid, 'typing')
        time.sleep(1)


	if (os.path.exists(log_file) ):
	     i = 0	
	     old_load_info = "" #to compare and send only new info
	     while True:
		print i #DEBUG
		text_log = ""
		load_info = ""
		text_log = os.popen(" tail -n 100 "+ log_file+" | grep -E 'DL|(OK)|SEED' | tail -n 1 ") #|ERR to errors updater
		load_info = text_log.read()
		if (len(load_info) > 4 and (load_info != old_load_info)):
			print (load_info)
			if(re.search('.*DL.*', load_info)):
			    bot.send_message(cid, load_info)
			    i = 0	
			    old_load_info = load_info
			elif (re.search('.*(OK).*', load_info)):
			    print load_info
			    bot.send_message(cid, "Download complete")
			    userStep[cid] = 4	
			    send_files_to_user(m) #to store where user is			    
			    break
			elif(re.search('.*SEED.*', load_info)):
			    bot.send_message(cid, "Downloaded")
			    userStep[cid] = 4
			    send_files_to_user(m)
			    break
			elif(re.search('.*ERR.*', load_info)):
			    bot.send_message(cid, "Huston, we have a problem :(")
                            bot.send_message(cid, load_info)
                            userStep[cid] = 1
                            break
			elif (i >= 16):  #make user calm every 1 min 20 sec
		            i = 0
		    	    bot.send_chat_action(cid, 'typing')
		    	    bot.send_message(cid, "Files are comming...")
		else:
			if(i >= 16):
                            i = 0
                            bot.send_chat_action(cid, 'typing')
                            bot.send_message(cid, "Files are comming...")

		time.sleep(5)#wainting for new info
		i = i + 1
		continue
	else:
	    print "Skip downloading"			


#watch every 10 seconds and show info only if updates
#other script to send info?
	
		
#####################################



@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 4)
def send_files_to_user(m):
    cid = str(m.chat.id)
    files_folder = download_folder + cid
    print "Folder with files:" + files_folder	
    if (os.path.exists(files_folder)): 
	i = 0
	files = []
	allFilesString = ""
	#create keyboard for all files IDs
        filesToDownloadSelect = types.ReplyKeyboardMarkup(one_time_keyboard=False)
        filesToDownloadSelect.add('Recieve all')

	for root, subdirs, files_os in os.walk(files_folder): #all folders
          for file in files_os:
             files.append(root+'/'+file.encode(sys.getfilesystemencoding()))
	files.sort()
	for f in files:
	    file = str(f)	
	    iter = str(i)
            allFilesString = allFilesString + "\n"+iter+". "+file
            filesToDownloadSelect.add(iter)
	    i = i + 1
	bot.send_message(cid, "Files to send:",reply_markup=hideBoard)
	
	if len(allFilesString) > 0:
	    bot.send_message(cid, allFilesString, reply_markup=filesToDownloadSelect)
            bot.send_message(cid, "Please select which files you want to recieve")
	    userStep[m.chat.id] = 5
	else:
	    bot.send_message(cid, "No files to send :( My bad")
	    print "allFilesString is empty, smthng with directory?"
	    userStep[m.chat.id] = 1	

    else:
	bot.send_message(cid, "Sorry, but something goes wrong and files is not avaliable to send :(")
    	bot.send_message(cid, "You can try again or later")	
	userStep[m.chat.id] = 1

#Send files to users
@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 5)
def send_file(m):
    cid = str(m.chat.id)
    number = m.text
    files_folder = download_folder + cid
    print "Send file from: "+ files_folder
    if (os.path.exists(files_folder)):
	i = 0
	files = []
        for root, subdirs, files_os in os.walk(files_folder): #get all files
          for file in files_os:
            files.append(root+'/'+file.encode(sys.getfilesystemencoding()))

	files.sort()
	bot.send_message(cid, "Ok, I send..")

	for file in files:
          if (os.path.getsize(file) > 52428800): # > 50Mb
           print "zZz big files.."
	   bot.send_message(cid, "Sotty, not telegram doesn't allow send files more then 50Mb. We're working around")
#          cmd = ['split', '-d',  '-b' ,'48M' , file , file + '.' ]
#          subprocess.Popen(cmd).wait()
#          cmd = ['rm', file]
#          subprocess.Popen(cmd).wait()
	  else:
	   doc = open(file, 'rb')
	   bot.send_document(cid, doc)	   
	    
	    

	    
    else:
	bot.send_message(cid, "Sorry, but something goes wrong and files is not avaliable to send :(")
        bot.send_message(cid, "You can try again or later")
        userStep[m.chat.id] = 1





# default handler for every other text
@bot.message_handler(func=lambda message: True, content_types=['text'])
def command_default(m):
    # this is the standard reply to a normal message
    bot.send_message(m.chat.id, "I don't understand \"" + m.text + "\"\nMaybe try the help page at /help")


bot.polling()
