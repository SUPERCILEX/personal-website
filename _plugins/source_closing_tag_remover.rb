Jekyll::Hooks.register([:pages, :posts], :post_write) do |page|
  file = page.destination(page.site.dest)

  content = File.read file
  content = content.gsub('</source>', '')

  File.write(file, content)
end
