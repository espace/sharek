$(document).ready(function() {
  $(".rate").live("click",function(){
    $.ajax({
            type:"POST",
            url :"/sharek/article_vote/",
            data:{'article':$(this).attr('id'),'type': $(this).attr('vote') ,'csrfmiddlewaretoken': $('#csrf_token').attr('value')},
            dataType:"json",
            error:function(data){},
            success:function(data){
            $(".like.article"+"."+data.article).text(data.p);  
            $(".dislike.article"+"."+data.article).text(data.n);
            if (data.vote == 1)
              {
                $(".like.rate"+"."+data.article).addClass("active")
                $(".dislike.rate"+"."+data.article).removeClass("active")
        
                $(".like.rate"+"."+data.article).removeClass("disabled")
                $(".dislike.rate"+"."+data.article).addClass("disabled")
              }
              else
              {
                $(".dislike.rate"+"."+data.article).addClass("active")
                $(".like.rate"+"."+data.article).removeClass("active")
        
                $(".dislike.rate"+"."+data.article).removeClass("disabled")
                $(".like.rate"+"."+data.article).addClass("disabled")
              }
            },
          });
  });
});