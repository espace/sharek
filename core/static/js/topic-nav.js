              $(document).ready(function() {
                
               // $(".topic").live("change",function(){
    
               //       $('.mada-title a:first-child').waypoint(function(event) {
               //              var faslText = $(this).html()
               //              // alert(faslText);
               //               $('.chapter-s').stop().fadeIn("slow").html(faslText);
               //                $('.topic').live()


               //        }, {
               //          // triggerOnce: true,
               //          offset: 'bottom-in-view'
               //          // offset: '50%'
               //        });


               //   });

               /// fasl detection 
              
              $('.mada-title a:first-child').waypoint(function(event) {
                            var faslText = $(this).html()
                            // alert(faslText);
                             $('.chapter-s').stop().fadeIn("slow").html(faslText);
                              $('.topic').live()


                      }, {
                        // triggerOnce: true,
                        offset: 'bottom-in-view'
                        // offset: '50%'
                      });



              /// floating note
               var $postShare = $('.floatingSocial');
                var descripY = parseInt($('.content').offset().top);
        
        
                $(window).scroll(function() { 
                    var scrollY = $(window).scrollTop();
                    var fixedShare = $postShare.css('position') == 'fixed';
                    if ($('.floatingSocial').length > 0) {
                        if (scrollY > descripY && !fixedShare) {
                            $postShare.stop().fadeIn("slow").css({
                                position: 'fixed',
                                bottom: 20,
                                display:'block'
                            });
                        } else if (scrollY < descripY && fixedShare) {
                            $postShare.stop().fadeOut("slow").css({
                                position: 'relative',
                                display:'none'
                            });
                        }
                    }



                });
               

               // var $postShare2 = $('.addthis_toolbox');


               //    $(window).scroll(function() { 
               //      var scrollY = $(window).scrollTop();
               //      var fixedShare = $postShare2.css('position') == 'fixed';
               //      if ($('.addthis_toolbox').length > 0) {
               //          if (scrollY > descripY && !fixedShare) {
               //              $postShare2.css({
               //                  position: 'fixed'
               //              });
               //          } else if (scrollY < descripY && fixedShare) {
               //              $postShare2.css({
               //                  position: 'absolute'
               //              });
               //          }
               //      }



               //  });
                  










              });
