module ImageCompression
  Jekyll::Hooks.register :site, :post_write do |site|
    system "python3 .build/css_compressor.py #{Jekyll::env}" or raise 'CSS compression failed.'
  end
end
