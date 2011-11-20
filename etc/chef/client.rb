log_level                :info
log_location             STDOUT
node_name                '<your_new_client_name>'
client_key               '/etc/chef/client.pem'
validation_client_name   '<your_new_client_name>'
validation_key           '/etc/chef/validation.pem'
chef_server_url          'http://<your_chef_server_name>:4000'
cache_type               'BasicFile'
cache_options( :path => '/etc/chef/checksums' )
