import graphene
from graphene_django import DjangoObjectType

from .models import Link
from users.schema import UserType
from links.models import Link, Vote
from graphql import GraphQLError
from django.db.models import Q

class LinkType(DjangoObjectType):
    class Meta:
        model = Link

class VoteType(DjangoObjectType):
    class Meta:
        model = Vote

class Query(graphene.ObjectType):
    # Add the first and skip parameters
    links = graphene.List(
        LinkType,
        search=graphene.String(),
        first=graphene.Int(),
        skip=graphene.Int(),
    )
    votes = graphene.List(VoteType)

    # Use them to slice the Django queryset
    def resolve_links(self, info, search=None, first=None, skip=None, **kwargs):
        qs = Link.objects.all()

        if search:
            filter = (
                Q(url__icontains=search) |
                Q(setup__icontains=search) |
                Q(punchline__icontains=search) |
                Q(type__icontains=search)
            )
            qs = qs.filter(filter)

        if skip:
            qs = qs[skip:]

        if first:
            qs = qs[:first]

        return qs

    def resolve_votes(self, info, **kwargs):
        return Vote.objects.all()

    
class CreateLink(graphene.Mutation):
    id = graphene.Int()
    url = graphene.String()
    setup = graphene.String()
    punchline = graphene.String()
    type = graphene.String()
    posted_by = graphene.Field(UserType)

    class Arguments:
        url = graphene.String()
        setup = graphene.String()
        punchline = graphene.String()
        type = graphene.String()

    def mutate(self, info, url, setup, punchline, type):
        user = info.context.user or None

        link = Link(
            url=url,
            setup=setup,
            punchline=punchline,
            type=type,
            posted_by=user,
        )
        link.save()

        return CreateLink(
            id=link.id,
            url=link.url,
            setup=link.setup,
            punchline=link.punchline,
            type=link.type,
            posted_by=link.posted_by,
        )

class CreateVote(graphene.Mutation):
    user = graphene.Field(UserType)
    link = graphene.Field(LinkType)

    class Arguments:
        link_id = graphene.Int()

    def mutate(self, info, link_id):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('You must be logged to vote!')

        link = Link.objects.filter(id=link_id).first()
        if not link:
            raise GraphQLError('Invalid Link!')

        Vote.objects.create(
            user=user,
            link=link,
        )

        return CreateVote(user=user, link=link)

#4
class Mutation(graphene.ObjectType):
    create_link = CreateLink.Field()
    create_vote = CreateVote.Field()