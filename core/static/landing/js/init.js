

   $(document).ready(function(){
        
/*
my answer to the following question:
http://stackoverflow.com/questions/5646522/any-raphaeljs-guru-knows-how-to-draw-this-image

me:
http://twitter.com/basecode
follow me if you like svg+js+html5+objc+cocos2d related topics
*/
var prgress_indicator = $("#prgress_indicator").val();
var prgress_Number = $("#prgress_Number").val();
var text  = ' عدد التعليقات <br /><strong>'+prgress_Number+'</strong>'; 
var title = $('#prgress_Percentage_Number').val();
var text2 = ' <strong class="sec">'+title+'</strong>'; 

$(".fir").html(text); // to Set the number of mosharakat for the first time.



Raphael.fn.zeroToTenArc = function (x, y, radius, value) {
  var angle = 0;
  var endAngle = (value*360)/10;
  var path = "";
  var clockwise = -1;
  var translate = Math.PI/2;
  
  while(angle <= endAngle) {
        
    var radians= (angle/180) * Math.PI + translate;
    var cx = x + Math.cos(radians) * radius;
    var cy = y + Math.sin(radians) * radius * clockwise;
    
    path += (angle === 0) ? "M" : "L";
    path += [cx,cy];
    angle += 1;
 }
  return this.path(path);
};

var canvas = Raphael("canvas", 300, 250);

var amin1 = canvas.zeroToTenArc(160, 130, 100, 10).attr({ stroke : "#eee", "stroke-width" : 12 });

var amin2 = canvas.zeroToTenArc(160, 130, 100, prgress_indicator).attr({ stroke : "#79af01", "stroke-width" : 22 });

canvas.circle(160, 130, 80).attr({ stroke: 'none', fill: '#e5e5e5' });

// Creates circle at x = 50, y = 40, with radius 10



        amin2.mouseover(function(){
                this.animate({ 'stroke-width': 30, opacity: 0.75 }, 1000, 'elastic');
        this.toFront();
              
            $('.fir').stop().animate({ opacity: 0 }, 100, function(){
                      $(this).html(text2).attr('rel', text).removeAttr('title').animate({ opacity: 1 });
                  ;}); 



            }).mouseout(function(){
        	this.stop().animate({ 'stroke-width': 22, opacity: 1 }, 250*4, 'elastic');
        
             $('.fir').stop().animate({ opacity: 0 }, 100, function(){
                  $(this).html(text).attr('title', text2).removeAttr('rel').animate({ opacity: 1 })
                  ;});

            });


            // function swapTitleAttr  () {
             
              
            
              
              $('.fir').hover(function one (){

                  $(this).stop().animate({ opacity: 0 }, 0, function(){
                      $(this).html(text2).attr('rel', text).removeAttr('title').animate({ opacity: 1 });
                  ;}); 


              },function two (){

                 $(this).stop().animate({ opacity:0 }, 0, function(){
                  $(this).html(text).attr('title', text2).removeAttr('rel').animate({ opacity: 1 })
                  ;});     
              });


        });//dom




      
