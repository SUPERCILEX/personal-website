module PostRedirects
  class Generator < Jekyll::Generator
    priority :highest

    def generate(site)
      site.posts.docs.each_with_index do |post, index|
        date_qualified_post_id =
          (post.data['date']&.strftime('%Y/%m/%d') || 'drafts') + '/' + post.data['slug'] + '/'
        post_category_path = post.data['categories'].map { |category|
          category.downcase.tr(' ', '-')
        }.join('/')

        post_redirects = [
          '/blog/' + (index + 1).to_s + '/',
          '/blog/' + date_qualified_post_id,
          '/blog/' + post_category_path + '/' + date_qualified_post_id,
          '/' + date_qualified_post_id,
        ]

        post.data['redirect_from'] = Array(post.data['redirect_from']) + post_redirects
      end
    end
  end

  Jekyll::Hooks.register :site, :post_write do |site|
    if Jekyll::env =~ /production/i
      # Jekyll's hook ordering is garbage so we have to re-run compression here just to make sure
      # it actually ran. Couldn't get the priority param to work.
      system 'python3 .build/image_compressor.py' or raise 'Image compression failed.'

      system 'python3 .build/firebase_redirect_inliner.py' or raise 'Redirect creation failed.'
      system 'python3 .build/downgrade_seo_image_resolution.py' or raise 'SEO image res downgrader failed.'
    end
  end
end
