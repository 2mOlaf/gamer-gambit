const Discord = require('discord.js');
const auth = require('./auth.json');
const low = require('lowdb');
const log = require('./gg-bot.js');
const FileSync = require('lowdb/adapters/FileSync');
// WARNING :: Production Database!!!
const adapter = new FileSync('itch_pak.json')
const db = low(adapter);

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
    return output;
}

// Initialize Discord Bot
const bot = new Discord.Client();

bot.on('ready', () => {
    console.log(`Logged in as ${bot.user.tag}!`);
});

bot.on('message', (message) => {
    if (message.author.username != bot.user.username) {
        botname = bot.user.username;
        msg = message.content.toLowerCase();
        mention = message.mentions.users.first();
        
        if (mention != bot.user.id) { return; }

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
        } else { message.reply("I did not understand that.") }
    }
});

bot.login(auth.token);