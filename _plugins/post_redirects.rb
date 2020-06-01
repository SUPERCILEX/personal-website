module PostRedirects
  class Generator < Jekyll::Generator
    priority :highest

    def generate(site)
      site.posts.docs.each_with_index do |post, index|
        post_redirects = [
          '/blog/' + (index + 1).to_s + '/',
          '/' + post.data['date'].strftime("%Y/%m/%d") + '/' + post.data['slug'] + '/'
        ]

        post.data['redirect_from'] = Array(post.data['redirect_from']) + post_redirects
      end
    end
  end
end
