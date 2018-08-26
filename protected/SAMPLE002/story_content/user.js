function ExecuteScript(strId)
{
  switch (strId)
  {
      case "5trz20Qi2HJ":
        Script1();
        break;
  }
}

function Script1()
{
  var vars = {};

var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {

		vars[key] = value;
    
	});
    
var ID = vars['ID'];


var player = GetPlayer();
var score = player.GetVar("ScorePercent");

var output = '/score/' + ID;

var href = 'https://roodee-data.com:448' + output 

document.body.innerHTML += '<form id="scoreform" action="' + href + '" method="post"><input type="hidden" name="score" value="' + score + '"></form>';
document.getElementById("scoreform").submit();
}

