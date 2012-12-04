$(document).ready(function() {
  $(".option").live("click",function(){
    $.ajax({
            type:"POST",
            url :"/sharek/poll_select/",
            data:{'option_id':$(this).attr('value'),'state': $(this).is(':checked') ,'csrfmiddlewaretoken': $('#csrf_token').attr('value')},
            dataType:"json",
            error:function(data){},
            success:function(data){
              $(".count"+"."+data.option_id).text(data.count+"  صوتا");
            },
          });
  });
});