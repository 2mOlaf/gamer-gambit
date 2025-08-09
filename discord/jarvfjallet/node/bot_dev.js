// const Discord = require('discord.js');
const { Client, Intents } = require('discord.js');
const { token } = require('./auth.json');
const low = require('lowdb');
const FileSync = require('lowdb/adapters/FileSync');
const adapter = new FileSync('itch_pak_dev.json')
const db = low(adapter);
// Initialize Discord Bot
const client = new Client({
    intents: [Intents.FLAGS.GUILDS, Intents.FLAGS.GUILD_MESSAGES, Intents.FLAGS.GUILD_MESSAGE_REACTIONS],
});

client.once('ready', () => {
    console.log(`Logged in as ${client.user.tag}!`);
});

db.defaults({ games: [] }).write();

function rand_db(userID) {
    console.log(userID+" rolled the dice");
    const sample_game = db.get('games').filter({reviewer: ''}).sample().value();
    db.get('games')
    .find({id: sample_game.id})
    .assign({'reviewer': userID, 'assigndate': Date.now()})
    .write();
    console.log("assigned "+sample_game.gameName);
    return sample_game;
}

function status(userID, username) {
    console.log(username+" requested game status");
    var statusID = db.get('games')
    .filter({ reviewer: userID })
    .value();
    statusID.forEach(entry => { console.log(entry.gameName)});

    var statusName = db.get('games')
    .filter({ reviewer: username })
    .value();
    statusName.forEach(entry => { console.log(entry.gameName)});

    const status = statusID.concat(statusName);
    console.log("Total: "+status.length);
    const currentDate = new Date();
    
    const act = "▶️ ";
    const wait = "⏸ ";
    const done = "⏹ ";
    const rec = "⏺ ";

    var query = [act+"Active; "+wait+"Waiting; "+done+"Done\n"];
    
    status.forEach(item => {
        var reviewdate = new Date(item.reviewdate);
        var assigndate = new Date(item.assigndate);

        if ( reviewdate != '' && reviewdate < currentDate) {
            query.push(done+item.gameName+" by "+item.devName+" <"+item.gameUrl+">");
        } else if ( assigndate.getDate() > currentDate.getDate()-7) {
            query.push(act+item.gameName+" by "+item.devName+" <"+item.gameUrl+">");
        } else if ( item.reviewdate == '' ) {
            query.push(wait+item.gameName+" by "+item.devName+" <"+item.gameUrl+">");
        } else if ( assigndate.getDate() == currentDate.getDate() ) {
            query.push(rec+item.gameName+" by "+item.devName+" <"+item.gameUrl+">");
        } else {
            query.push("??? "+item.gameName+" by "+item.devName+" <"+item.gameUrl+">");
        }
    });

    var output = query.join('\n');

    if (output == null) {
        console.log(username+" has no entries. Returning the bad news.");
        output = "```css\nWARNING!\nYou have no games recorded. If you want to stay relevant here, you must first get involved.\nTry: '@Gamer Gambit hit me' (the mention has to key to the actual bot user)\n```"
    }

    return output;
}


/**
 * Discord.js Interaction feature is specific to slash commands, I think
**/
client.on('interactionCreate', async interaction => {
    if (!interaction.isCommand()) {
        console.log("Command was empty");
        return;
    }

    console.log(interaction);

    const { commandName } = interaction;

	if (commandName === 'ping') {
		await interaction.reply('Pong!');
	} else if (commandName === 'beep') {
		await interaction.reply('Boop!');
	}
});

client.on('message', (message) => {
    // console.log(message);
    // const { message } = message;
    console.log(message.content);

    if (message.author.username != client.user.username) {
        botname = client.user.username;
        msg = message.content.toLowerCase();
        mention = message.mentions.users.first();
        
        if (mention != client.user.id) { 
            console.log(`Ignoring messages for ${mention}.`);
            return;
        }

        msg = message.cleanContent.substr(botname.length + 2,message.length)

        if (msg.startsWith("hit ")) {
            // WARNING :: Function finds *AND ASSIGNS* target to user!!
            var sample = rand_db(message.author.id);
            // message.delete();
            message.author.send("**" + sample.gameName + "**>\n(" + sample.gameUrl + ")");
            message.reply("**" + sample.gameName + "** has been assigned to you!\n(" + sample.gameUrl + ")");
        } else if (msg.startsWith("status ") || msg === "status") {
            // Let's also extend this to support targeting a user (e.g. @Gamer Gambit status 2mOlaf)
            // Also, would you rather this be a PM, or is it better to be visible in the channel?
            message.reply("your assigned games are:\n"+status(message.author.id,message.author.username));
        } else if (msg === 'help') {
            message.reply("You can either use _hit me_ or _status_ for now.\nI do not _do_ trim, so keep your commands tidy.");
        } else { message.reply("I did not understand:\n> "+msg) }
    } else {
        console.log(`Message came from ${message.author.username}. Abandoning...`);
    }
});

client.login(token);