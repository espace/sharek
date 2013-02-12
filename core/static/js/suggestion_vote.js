$(document).ready(function() {
  $(".rate").live("click",function(){
    $.ajax({
            type:"POST",
            url :suggestion_vote_var,
            data:{'article':$(this).attr('art_id'),'suggestion':$(this).attr('id'),'type': $(this).attr('vote') ,'csrfmiddlewaretoken': $('#csrf_token').attr('value')},
            dataType:"json",
            error:function(data){},
            success:function(data){
            $(".like.suggestion"+"."+data.suggestion).text(data.p);  
            $(".dislike.suggestion"+"."+data.suggestion).text(data.n);
            if (data.vote == 1)
              {
                $(".like.rate"+"."+data.suggestion).addClass("active")
                $(".dislike.rate"+"."+data.suggestion).removeClass("active")
        
                $(".like.rate"+"."+data.suggestion).removeClass("disabled")
                $(".dislike.rate"+"."+data.suggestion).addClass("disabled")
              }
              else
              {
                $(".dislike.rate"+"."+data.suggestion).addClass("active")
                $(".like.rate"+"."+data.suggestion).removeClass("active")
        
                $(".dislike.rate"+"."+data.suggestion).removeClass("disabled")
                $(".like.rate"+"."+data.suggestion).addClass("disabled")
              }
            },
          });
  });
});