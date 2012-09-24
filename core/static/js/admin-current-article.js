$(document).ready(function() {
  $(".field-current").live("click",function(){
    
    $action = $($(this).children()[0])
    current_state = $action.is(':checked');
    $('.field-current').each(function(index) {
      var $temp = $($(this).children()[0])
      $temp.val(false);  
      $temp.attr('checked', false);
    });
    
    var $current = $($(this).children()[0])
    if (current_state == "on" || current_state == true){  
      $current.val(true);
      $current.attr('checked', true);
    }else{
      $current.val(false);
      $current.attr('checked', false);
    }
  });
});