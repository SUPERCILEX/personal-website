Jekyll::Hooks.register :site, :pre_render do |site|
  post_paths = Set[]
  site.posts.docs.each do |post|
    if post_paths.include?(post.id)
      raise NameError, 'Conflicting post paths found: ' + post.id
    end

    post_paths.add(post.id)
  end
end
