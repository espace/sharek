              $(document).ready(function() {
                var $postShare = $('.floatingSocial');
                var descripY = parseInt($('.content').offset().top);
        
        
                $(window).scroll(function() { 
                    var scrollY = $(window).scrollTop();
                    var fixedShare = $postShare.css('position') == 'fixed';
                    if ($('.floatingSocial').length > 0) {
                        if (scrollY > descripY && !fixedShare) {
                            $postShare.stop().css({
                                position: 'fixed',
                                top: 0,
                                display:'block'
                            });
                        } else if (scrollY < descripY && fixedShare) {
                            $postShare.css({
                                position: 'relative',
                                display:'none'
                            });
                        }
                    }
                });
              });
