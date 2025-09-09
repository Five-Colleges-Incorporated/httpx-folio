# httpx-folio

FOLIO related niceties for the [next generation HTTP client](https://www.python-httpx.org/) for Python.

### Not invented here?

There are many existing and excellent FOLIO clients out there for Python.
* https://github.com/FOLIO-FSE/folioclient
* https://github.com/balljok/pyfolioclient
* https://github.com/tobi-weber/foliolib

This library is in no way intended to be a replacement for them.
Instead it is taking a minimalist approach to configuring a raw HTTPX client for FOLIO with a focus on resilience, stability, and observability.
If you can use a higher-level client to accomplish your goal you will have a better time using one.
For all other times httpx-folio is here for you.

As of 0.2.0 it supports
* [Sync] Okapi and Eureka with a single tenant
* Query and paging parameter handling

Future
* [Async] Okapi and Eureka with a single tenant
* [(A)Sync] Okapi and Eureka with ECS support
* [(A)Sync] Edge with a single tenant and ECS support

The hope is that other (existing and new) clients can build on top of this one to avoid re-inventing these wheels.

### The origin
This code started out in the LDLite repository as it was a little too weird to use the existing python clients.
