module ImageCompression
  Jekyll::Hooks.register :site, :post_write do |site|
    system 'python3 .build/image_compressor.py' or raise 'Image compression failed.'
  end
end
