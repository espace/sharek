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
              });
