function ExecuteScript(strId)
{
  switch (strId)
  {
      case "6mFBvbbUZPI":
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

document.body.innerHTML += '<iframe width="0" height="0" border="0" name="dummyframe" id="dummyframe"></iframe><form id="scoreform" target="dummyframe" action="' + href + '" method="post"><input type="hidden" name="score" value="' + "100" + '"></form>';
document.getElementById("scoreform").submit();
}

