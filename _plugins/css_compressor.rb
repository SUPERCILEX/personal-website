module ImageCompression
  Jekyll::Hooks.register :site, :post_write do |site|
    env = site.config['env']
    system "python3 .build/css_compressor.py #{env}" or raise 'CSS compression failed.'
  end
end
