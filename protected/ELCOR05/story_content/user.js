function ExecuteScript(strId)
{
  switch (strId)
  {
      case "6r2XRpCk4JD":
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

var href = 'https://roodee-data.com:448' + output;

var iframe = document.createElement("iframe");
iframe.name = 'roodee_iframe';
iframe.style="width:0; height:0; border:0; border:none"
var form = document.createElement("form");
document.body.appendChild(iframe);
document.body.appendChild(form);
form.method = "POST";
form.action = href;
form.target = "roodee_iframe";
var element1 = document.createElement("INPUT");         
element1.name="score"
element1.value = score;
element1.type = 'hidden';
form.appendChild(element1);
form.submit();
}

