fetch("./index.json").then(response => response.json()).then(data => {
    if (data["saves"]["share_history"]==null){
        data["saves"]["share_history"] = []
    }
    console.log(data)
    var history_table = document.getElementById("history-table")
    for (var item of data["saves"]["share_history"]){
        var row = history_table.insertRow(-1)
        row.insertCell(-1).innerText = item["time"]
        row.insertCell(-1).innerHTML = `<a href='${item["url"]}' target="_blank">${item["name"]}</a>`
    }
    console.log(document.getElementById("server-container"))
})
