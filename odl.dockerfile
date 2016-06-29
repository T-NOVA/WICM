FROM opendaylight/odl:4.1.0
RUN sed -ie "s/featuresBoot=.*/featuresBoot=config,standard,region,package,kar,ssh,management,odl-vtn-manager,odl-vtn-manager-rest,odl-mdsal-apidocs,odl-dlux-all/g" etc/org.apache.karaf.features.cfg

