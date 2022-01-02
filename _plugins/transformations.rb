Jekyll::Hooks.register :site, :post_write do |site|
  system "python3 .build/css_compressor.py #{Jekyll::env}" or raise 'CSS compression failed.'
  system 'python3 .build/image_compressor.py' or raise 'Image compression failed.'
  if Jekyll::env =~ /production/i
    system 'python3 .build/firebase_redirect_inliner.py' or raise 'Redirect creation failed.'
    system 'python3 .build/downgrade_seo_image_resolution.py' or raise 'SEO image res downgrader failed.'
    system 'python3 .build/html_compressor.py' or raise 'HTML compression failed.'
  end
end
