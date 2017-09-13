import telebot
from telebot import types
import time
import re
import urllib
import os
import os.path
 

TOKEN = '411001654:AAFG3y_C20jslSqKqUe0Yei0WNW7y55INfM'

knownUsers = []  # todo: save these in a file,
userStep = {}  # so they won't reset every time the bot restarts

commands = {  # command description used in the "help" command
              'start': 'Get used to the bot',
              'help': 'Gives you information about the available commands',
              'downloadTorrent': 'To start proccess of downloading'
}

howDownloadTorrentFileSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True)  # create the image selection keyboard
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
#        return 0
        return userStep[uid]

# only used for console output now
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
    bot.send_message(cid, "Returned. Please make a choice", reply_markup=howDownloadTorrentFileSelect)  # show the keyboard
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
	file_name = "/tbot/torrents/" + link.split('/')[-1]
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
	    file_location = '/tbot/torrents/'+file_info.file_path
	    link = "https://api.telegram.org/file/bot"+TOKEN+"/"+file_info.file_path
	    urllib.urlretrieve (link, file_location)	
	    bot.send_message(cid, "Ok, file " + file_name + " recived ")	
	    f = os.popen("transmission-show '" + file_location + "' | grep -v '/tbot/torrents/' ")
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


# default handler for every other text
@bot.message_handler(func=lambda message: True, content_types=['text'])
def command_default(m):
    # this is the standard reply to a normal message
    bot.send_message(m.chat.id, "I don't understand \"" + m.text + "\"\nMaybe try the help page at /help")


##########TORRENT DOWNLOAD############

def downloader(m, link):
	cid = m.chat.id
	bot.send_message(cid, "Proccessing..."+link)
	bot.send_chat_action(cid, 'typing')
	
	
	
#####################################





bot.polling()
