const low = require('lowdb')
const FileSync = require('lowdb/adapters/FileSync')

const adapter = new FileSync('itch_pak.json')
const db = low(adapter)

// const fs = require('fs')
// const Memory = require('lowdb/adapters/Memory')

// const db = low(
//   process.env.NODE_ENV === 'test'
//     ? new Memory()
//     : new FileSync('itch_pak_dev.json')
// )

db.defaults({ games: [] })
  .write()

db._.mixin({
upsert: function(arr, obj, arg) {
    let item;
    for (let i = 0; i < arr.length; i++) {
        for (let j = 0; j < arg.length; j++) {
            if(obj[arg[j]] !== arr[i][arg[j]]){
                item = undefined;
                break;
            } else {
                item = i;
            }
        }
    }

    if(arr[item] === undefined){
        arr.push(obj);
    } else {
        for (let key in arr[item]) {
            if(!obj[key]){
                delete arr[item][key];
            }
        }
        Object.assign(arr[item], obj);
    }
    return arr;
    }
})

// db.get('games')
// .upsert({id: 647, gameUrl: "https://fractal-phase.itch.io/sky-rogue", thumbUrl: "https://img.itch.zone/aW1nLzI0MDczNjMucG5n/300x240%23c/UtKpC9.png", windows: true, mac: true, linux: true, gameName: "Sky Rogue", gameHost: "fractal-phase.itch.io", devName: "Fractal Phase", devUrl: "https://fractal-phase.itch.io", shortText: "A fwooshy, intense, procedurally generated fly-em-up", reviewer: "", thumbnail: "", reviewurl: "", reviewdate: ""}, ["id", "gameUrl", "thumbUrl", "windows", "mac", "linux", "gameName", "gameHost", "devName", "devUrl", "shortText", "reviewer", "thumbnail", "reviewurl", "reviewdate"])
// .write();

// const findr = db.get('games')
// .find({reviewer: ''})
// .value();
// console.log(findr);

const game = "VoltAge:Genesis"

// db.get('games')
// .find({gameName: game})
// // .assign({reviewurl: 'https://youtu.be/W7Gmy07HPzs', reviewdate: Date.parse('06-23-2020')})
// .assign({reviewer: '595642909358030861', assigndate: Date.now()})
// .write();

function timestamps() {
    var games = db.get('games')
    .reject({ 'reviewdate': '' })
    .value();

    games.forEach(element => {
        if (element.assigndate == null || element.assigndate == false) {
            // console.log("We would change "+element.gameName)
            db.get('games').find({'id': element.id}).assign({'assigndate':element.reviewdate}).write();
        } else {
            console.log(element.gameName+"\t"+element.reviewdate+"\t"+element.assigndate);
        }
    });
}

timestamps();

function status(userID, username) {
    var statusID = db.get('games')
    .filter({ reviewer: userID })
    .value();

    var statusName = db.get('games')
    .filter({ reviewer: username })
    .value();

    const status = statusID.concat(statusName);
    const currentDate = new Date();
    
    status.forEach(element => {
        if (element.reviewdate != '') {
            var reviewdate = new Date(element.reviewdate);
        } else { var reviewdate = '' }
        if(reviewdate != '') {
            console.log("DONE: "+element.gameName+" by "+element.devName+" <"+element.gameUrl+">");
        } else if(reviewdate == '') {
            console.log("- "+element.gameName+" by "+element.devName+" <"+element.gameUrl+">");
        } else if(reviewdate != '' && reviewdate.toDateString() == currentDate.toDateString()) {
            console.log("REC: "+element.gameName+" by "+element.devName+" <"+element.gameUrl+">");
        } else { console.log('??? '+element.gameName+" by "+element.devName+" <"+element.gameUrl+">");}
    });
}

// console.log(status('173246256968105987','Red-One'));
// console.log(status('595642909358030861','2mOlaf'));

// db.set('games[3].reviewer','')
// .write();

// const sample_game = db.get('games').filter({reviewer: ''}).sample().value();
// db.get('games')
// .find({id: sample_game.id})
// //.assign({'reviewer': user, 'reviewdate': Date.now()})
// .value();
// console.log(sample_game.gameUrl + " assigned to user!")
// console.log(sample_game.id);